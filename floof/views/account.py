# encoding: utf8
import logging

from pyramid import security
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound
from webhelpers.util import update_params
import wtforms.form, wtforms.fields, wtforms.validators

from floof.forms import TimezoneField
import floof.lib.auth
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
from floof.model import Resource, Discussion, UserProfileRevision, IdentityURL, User, Role, meta

#import re
#
#from pylons import request, response, session, tmpl_context as c, url
#from pylons.controllers.util import abort
#from sqlalchemy.orm.exc import NoResultFound
#from urllib2 import HTTPError, URLError
#import wtforms.form, wtforms.fields, wtforms.validators
#
#from floof.lib import helpers
#from floof.lib.auth import CERT_CONFIDENCE_EXPIRY_SECONDS, CONFIDENCE_EXPIRY_SECONDS, fetch_stash_url, stash_keys
#from floof.lib.base import BaseController, render
#from floof.lib.helpers import redirect
#from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
#from floof import model

log = logging.getLogger(__name__)


class LoginForm(wtforms.form.Form):
    # n.b.: This is actually a name recommended by the OpenID spec, for ease of
    # client identification
    openid_identifier = wtforms.fields.TextField(u'OpenID URL or Webfinger-enabled email address',
            validators=[wtforms.validators.Required(u'Gotta enter an OpenID to log in.')]
            )
    return_key = wtforms.fields.HiddenField(u'Return Stash Key')

@view_config(
    route_name='account.login',
    request_method='GET',
    renderer='account/login.mako')
def account_login(context, request):
    form = LoginForm()
    #c.form.openid_identifier.data = c.auth.openid_url
    form.return_key.data = request.GET.get('return_key', None)
    return {'form': form}


@view_config(
    route_name='account.login_begin',
    request_method='POST')
def login_begin(context, request):
    """Step one of logging in with OpenID; redirect to the provider."""
    form = LoginForm(request.POST)

    if not form.validate():
        return render_to_response(
            'account/login.mako', {'form': form}, request=request)

    # Ensure the return key, if present and valid, will be passed
    # to openid_finish()
    return_url = request.route_url('account.login_finish')
    if form.return_key.data in floof.lib.auth.stash_keys(request.session):
        return_url = update_params(return_url,
            return_key=form.return_key.data)

    if 0 and c.user:
        # Logged-in user trying to update their OpenID expiry time
        if 'cert' in c.auth.satisfied:
            max_auth_age = CERT_CONFIDENCE_EXPIRY_SECONDS
        else:
            max_auth_age = CONFIDENCE_EXPIRY_SECONDS
        sreg = False
    else:
        # Logged-out user; may be about to register
        max_auth_age = False
        sreg = True

    try:
        return HTTPSeeOther(location=openid_begin(
                identifier=form.openid_identifier.data,
                return_url=return_url,
                request=request,
                max_auth_age=max_auth_age,
                sreg=sreg,
                ))
    except OpenIDError as exc:
        print exc
        form.openid_identifier.errors.append(exc.args[0])
        return render_to_response(
            'account/login.mako', {'form': form}, request=request)


@view_config(
    route_name='account.login_finish',
    request_method='GET')
def login_finish(context, request):
    """Step two of logging in; the OpenID provider redirects back here."""
    return_key = request.GET.get('return_key', None)
    if return_key:
        if return_key not in floof.lib.auth.stash_keys(request.session):
            abort(400, detail='Unknown return_key value')
        return_url=url(host=request.headers['host'],
                controller='account',
                action='login_finish',
                return_key=return_key,
                )
    else:
        return_url = request.route_url('account.login_finish')

    try:
        identity_url, identity_webfinger, auth_time, sreg_res = openid_end(
                return_url=return_url,
                request=request,
                )
    except OpenIDError as exc:
        # XXX wow this is N.G.
        return exc.args[0]

    if 0 and c.user:
        # An existing user is trying to re-auth
        if c.auth.openid_success(session, c.user.id, identity_url, auth_time):
            request.session.flash(u'Re-authentication successful', icon='user')
            if return_key:
                # Fetch a stashed POST request
                old_url = fetch_stash_url(session, return_key)
                if old_url:
                    log.debug('Following Return Key \'{0}\' to URL: {1}' \
                            .format(return_key, old_url))
                    redirect('{0}?return_key={1}'.format(old_url, return_key))
            redirect(url('/'))
        request.session.flash(u'Re-authentication unsuccessful.  Was \'{0}\' a '
                'valid OpenID URL registered against your account?' \
                .format(identity_url),
                level='error',
                )
        if return_key:
            redirect(url(controller='account', action='login', return_key=return_key))
        redirect(url(controller='account', action='login'))

    try:
        # Grab an existing user record, if one exists
        q = meta.Session.query(User) \
                .filter(User.identity_urls.any(url=identity_url))
        user = q.one()

        #log.debug('User {0} (#{1}) authenticated with OpenID URL "{2}"'
        #        .format(user.id, user.name, identity_url))

        # Log the successful authentication
        # TODO try/except
        request.auth.login_openid(user)
        auth_headers = []#security.remember(request, user.id)
        request.session.flash(
            u'Hello, {0}'.format(user.display_name or user.name),
            )#icon='user')
        return HTTPSeeOther(
            location=request.route_url('root'),
            headers=auth_headers)
        #redirect(url(controller='account', action='login'))

    except NoResultFound:
        # Nope.  Give a (brief!) registration form instead
        request.session['pending_identity_url'] = identity_url
        request.session.save()
        identity_webfinger = request.session.get('pending_identity_webfinger', None)

        # Try to pull a name and email address out of the SReg response
        form = RegistrationForm(
                username=sreg_res.get('nickname', u''),
                email=sreg_res.get('email', u''),
                timezone=sreg_res.get('timezone', u'UTC'),
                )
        form.validate()
        return render_to_response(
                'account/register.mako', {'form': form, 'identity_url': identity_url, 'identity_webfinger': identity_webfinger}, request=request)


@view_config(
    route_name='account.logout',
    request_method='POST')
def logout(context, request):
    """Logs the user out, if possible."""

    if 0 and c.auth.can_purge:
        c.auth.purge(session)
        helpers.flash(u'Logged out.',
              icon='user-silhouette')
    auth_headers = security.forget(request)
    return HTTPSeeOther(
        location=request.route_url('root'),
        headers=auth_headers,
    )


class RegistrationForm(wtforms.form.Form):
    username = wtforms.fields.TextField(u'Username', [
        wtforms.validators.Regexp(r'^[_a-z0-9]{1,24}$',
            message=u'Your username must be 1–24 characters and contain only '
            u'lowercase letters, numbers, and underscores.'
            ),
        ])
    email = wtforms.fields.TextField(u'Email Address', [
            wtforms.validators.Optional(),
            wtforms.validators.Email(message=u'That does not appear to be an email address.'),
            ])
    timezone = TimezoneField(u'Timezone')

    def validate_username(form, field):
        if meta.Session.query(User).filter_by(name=field.data).count():
            raise wtforms.validators.ValidationError(
                'Your username is already taken. Please try again.')

@view_config(
    route_name='account.register',
    request_method='POST')
def register(context, request):
    if request.user:
        # What are you doing here if you're already logged in?
        return HTTPSeeOther(location=request.route_url('root'))

    # Check identity URL
    identity_url = request.session.get('pending_identity_url')
    if not identity_url or \
       meta.Session.query(IdentityURL) \
            .filter_by(url=identity_url).count():

        # Not in the session or is already registered.  Neither makes
        # sense.  Bail.
        helpers.flash('Your session expired.  Please try logging in again.')
        return HTTPSeeOther(location=request.route_url('account.login'))

    identity_webfinger = request.session.get('pending_identity_webfinger', None)
    form = RegistrationForm(request.POST)
    if not form.validate():
        return render_to_response(
                'account/register.mako', {'form': form, 'identity_url': identity_url, 'identity_webfinger': identity_webfinger}, request=request)

    # Create db records
    base_user = meta.Session.query(Role).filter_by(name=u'user').one()
    resource = Resource(type=u'users')
    discussion = Discussion(resource=resource)
    user = User(
        name=form.username.data,
        email=form.email.data,
        role=base_user,
        resource=resource,
        timezone=form.timezone.data,
    )
    meta.Session.add_all((user, resource, discussion))

    openid = IdentityURL(url=identity_url)
    user.identity_urls.append(openid)

    log.info('User #{0} registered: {1}'.format(user.id, user.name))

    # Log 'em in
    del request.session['pending_identity_url']
    #####c.auth.openid_success(session, user.id, identity_url)

    # And off we go
    return HTTPSeeOther(location=request.route_url('root'))


class ProfileForm(wtforms.form.Form):
    profile = wtforms.fields.TextField(u'Profile')

@view_config(
    route_name='account.profile',
    permission='__authenticated__',
    renderer='account/profile.mako')
def profile(context, request):
    form = ProfileForm(request.POST)

    if request.method == 'POST' and form.validate():
        profile = request.user.profile = form.profile.data
        rev = UserProfileRevision(user=request.user, updated_by=request.user, content=profile)
        meta.Session.add(rev)

    return {}
