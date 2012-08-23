import logging

from hashlib import sha512

from oauthlib.common import add_params_to_uri, generate_token
from pyramid.httpexceptions import HTTPBadRequest, HTTPSeeOther
from pyramid.view import view_config, view_defaults

import wtforms

from floof import model
from floof.forms import FloofForm
from floof.lib.oauth import (
    OAUTH2_GRANT_CODE_LEN,
    OAuth2Error,
    AccessDeniedError,
    UnsupportedResponseTypeError,
    error_to_dict,
    expires_in,
    get_client,
    get_redirect_uri,
    may_get,
    must_get,
    parse_scope,
)
from floof.lib.stash import stash_post
from floof.views._workflow import FormWorkflow


log = logging.getLogger(__name__)


GRANT_EXPIRY_PERIOD = 60 * 5


def prepare_location(uri, params, state=None):
    if state:
        params['state'] = state
    return add_params_to_uri(uri, params.items())


@view_config(
    route_name='oauth2.authorize',
    context=OAuth2Error,
    renderer='error.mako')
def oauth2_authorization_error(error, request):
    try:
        source = request.POST if request.method == 'POST' else request.GET
        client = get_client(must_get(source, 'client_id'))
        location = may_get(source, 'redirect_uri')
        location = get_redirect_uri(client, location)
        state = may_get(source, 'state')

        if location == 'urn:ietf:wg:oauth:2.0:oob':
            raise error

    except OAuth2Error as e:
        # Hard fail -- we cannot safely redirect the UA back to the requesting
        # app, so drop the user to a failure message
        request.response.status = 400
        msg = (u'An invalid OAuth authorization request was encountered; for '
               'your protection the request has been cancelled.  The specific '
               'error was: "{0}"'.format(e.args[0]))
        return {
            'http_status': u'Invalid OAuth Authorization Request',
            'message': msg,
            'outstanding_principals': None,
        }

    # (Relatively) soft fail -- redirect to client endpoint with error
    location = prepare_location(location, error_to_dict(error), state)

    return HTTPSeeOther(location=location)


@view_defaults(
    route_name='oauth2.authorize',
    http_cache=0)
class OAuth2AuthorizationViews(FormWorkflow):
    class form_class(FloofForm):
        accept = wtforms.fields.SubmitField(u'Accept')
        cancel = wtforms.fields.SubmitField(u'Cancel')
        client_id = wtforms.fields.HiddenField()
        redirect_uri = wtforms.fields.HiddenField()
        response_type = wtforms.fields.HiddenField()
        scope = wtforms.fields.HiddenField()
        state = wtforms.fields.HiddenField()

    def make_form(self):
        return self.form_class(self.request, self.request.POST)

    @view_config(
        request_method='GET',
        renderer='/oauth_authorize.mako')
    def authorization_endpoint(self):
        request = self.request

        if not request.user:
            key = stash_post(request)
            request.session.flash(
                "You must log in if you wish to authorize thirdy party access "
                "to your account.", level='notice')
            location = request.route_url(
                'account.login', _query=[('return_key', key)])
            raise HTTPSeeOther(location=location)

        # It's hard to get a strong guarantee that the token request came over
        # TLS; this is a best-effort deal
        if request.scheme != 'https':
            raise HTTPBadRequest(
                'The authorization endpoint must be accessed over TLS')

        client_id = must_get(request.GET, 'client_id')
        given_rdr_uri = may_get(request.GET, 'redirect_uri')

        # Resolve the client and validate the redirect_uri;
        # on failure abort and present a warning to the user

        client = get_client(client_id)
        redirect_uri = get_redirect_uri(client, given_rdr_uri)

        response_type = must_get(request.GET, 'response_type')
        scopes = parse_scope(may_get(request.GET, 'scope'))
        state = may_get(request.GET, 'state')

        # On failure redirect the user to the redirect_uri with error codes

        if response_type != u'code':
            raise UnsupportedResponseTypeError(
                'The only supported authorization response_type is "code"')

        form = self.form_class(
            request,
            client_id=client.identifier,
            redirect_uri=given_rdr_uri,  # Need to know exactly what was passed
            response_type=response_type,
            scope=' '.join(scopes),
            state=state,
        )

        period = u'Indefinte'

        q = model.session.query(model.Scope)
        scope_desc = dict((s.name, s.description) for s in q.all())

        return dict(
            form=form,
            client=client,
            scopes=scopes,
            period=period,
            scope_desc=scope_desc,
        )

    @view_config(
        request_method='POST',
        permission='oauth.authorize',
        renderer='/oauth_authorize_show.mako')
    def authorization_endpoint_submit(self):
        request = self.request
        form = self.form

        if not form.validate():
            # XXX: Eh, what to do here?
            raise HTTPBadRequest('Something went wrong with your last action.')

        if not form.accept.data:
            raise AccessDeniedError('The user declined')

        client = get_client(form.client_id.data)
        given_rdr_uri = form.redirect_uri.data
        redirect_uri = get_redirect_uri(client, given_rdr_uri)
        response_type = form.response_type.data
        scopes = parse_scope(form.scope.data)
        state = form.state.data

        if response_type != u'code':
            raise UnsupportedResponseTypeError(
                'The only supported authorization response_type is "code"')

        code = generate_token(OAUTH2_GRANT_CODE_LEN)
        grant = model.OAuth2Grant(
            client=client,
            user=request.user,
            redirect_uri=redirect_uri,
            redirect_uri_supplied=bool(given_rdr_uri),
            code=sha512(code).hexdigest(),
            expires=expires_in(GRANT_EXPIRY_PERIOD),
            scopes=scopes,
        )
        model.session.add(grant)

        if redirect_uri == 'urn:ietf:wg:oauth:2.0:oob':
            return dict(client=client, code=code)

        location = prepare_location(redirect_uri, dict(code=code), state)

        return HTTPSeeOther(location=location)
