# encoding: utf8
import logging

from pyramid import security
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound
from webhelpers.util import update_params
import wtforms.form, wtforms.fields, wtforms.validators

from floof.forms import TimezoneField
import floof.lib.auth
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
from floof.model import Resource, Discussion, UserProfileRevision, IdentityURL, User, Role, meta

log = logging.getLogger(__name__)


class LoginForm(wtforms.form.Form):
    # n.b.: This is actually a name recommended by the OpenID spec, for ease of
    # client identification
    openid_identifier = wtforms.fields.TextField(
        u'OpenID URL or Webfinger-enabled email address',
        validators=[wtforms.validators.Required(u'Gotta enter an OpenID to log in.')])
    return_key = wtforms.fields.HiddenField(u'Return Stash Key')

@view_config(
    route_name='account.login',
    request_method='GET',
    renderer='account/login.mako')
def account_login(context, request):
    form = LoginForm()
    # XXX worth mentioning on this page how to log in with SSL, and offer a
    # crypto link if they already hit cancel and want to try again
    # XXX why do we need this?: form.openid_identifier.data = request.auth.openid_url
    # ^^^ that was to pre-fill the form in the (maybe) common case of re-auth
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
        # XXX need to do this, possibly use checkid_immediate instead
        if 'cert' in c.auth.satisfied:
            max_auth_age = CERT_CONFIDENCE_EXPIRY_SECONDS
        else:
            max_auth_age = CONFIDENCE_EXPIRY_SECONDS
        sreg = False
    else:
        # Someone either logging in or registering
        max_auth_age = False
        sreg = True

    try:
        return HTTPSeeOther(location=openid_begin(
                identifier=form.openid_identifier.data,
                return_url=return_url,
                request=request,
                max_auth_age=max_auth_age,
                sreg=sreg))
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
    return_url = request.route_url('account.login_finish')

    return_key = request.GET.get('return_key', None)
    if return_key is None:
        pass
    elif return_key in floof.lib.auth.stash_keys(request.session):
        return_url = update_params(return_url, dict(return_key=return_key))
    else:
        log.warning("Unknown return_key value: {0!r}".format(return_key))

    try:
        identity_url, identity_webfinger, auth_time, sreg_res = openid_end(
            return_url=return_url,
            request=request)
    except OpenIDError as exc:
        request.session.flash(
            u'Authentication unsuccessful: {0}'.format(exc),
            level='error', icon='key--exclamation')

        # XXX is a redirect to login_begin appropriate?
        location = request.route_url('account.login')
        if return_key:
            location = update_params(location, dict(return_key=return_key))

        return HTTPSeeOther(location=location)

    # Find who owns this URL, if anyone
    identity_owner = meta.Session.query(User) \
        .filter(User.identity_urls.any(url=identity_url)) \
        .limit(1).first()

    if request.user:
        # An existing user is logging in again!
        # Three possibilities here.

        if identity_owner == request.user:
            # Someone is just freshening up their cookie
            request.auth.login_openid(identity_owner)
            request.session.save()
            request.session.flash(u'Re-authentication successful', icon='user')

            if return_key:
                # XXX implement meee
                # Fetch a stashed POST request
                old_url = fetch_stash_url(session, return_key)
                if old_url:
                    log.debug('Following Return Key \'{0}\' to URL: {1}' \
                            .format(return_key, old_url))
                    redirect('{0}?return_key={1}'.format(old_url, return_key))

            return HTTPSeeOther(location=request.route_url('root'))

        elif identity_owner:
            # Someone is trying to log in as someone else.
            # XXX show a page with a button that will switch accounts...  unless you're using a cert...
            raise NotImplementedError
        else:
            # Someone is /either/ registering or adding a new openid to their current account
            # XXX show a page like the above, with the reg form plus a button to just add this openid to your account...  unless you're using a cert...
            raise NotImplementedError

    elif identity_owner:
        # A non-user has logged in successfully.  Bravo!
        log.debug("User {0!r} logged in via OpenID: {1!r}".format(identity_owner.name, identity_url))

        # Log the successful authentication
        # TODO try/except, catch all the things that can be thrown
        auth_headers = security.remember(request, identity_owner)
        request.session.flash(
            u"Hello, {0}".format(identity_owner.display_name or identity_owner.name),
            icon='user')
        # XXX this should ALSO probably do the return_key redirect, good grief
        return HTTPSeeOther(
            location=request.route_url('root'),
            headers=auth_headers)

    else:
        # A non-user has used a new OpenID; offer a registration form
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
            'account/register.mako',
            dict(form=form, identity_url=identity_url,
                identity_webfinger=identity_webfinger),
            request=request)


@view_config(
    route_name='account.logout',
    request_method='POST')
def logout(context, request):
    """Logs the user out, if possible."""

    # XXX if you're using a client cert, this should try hard to log you out
    # with the crypto api
    # XXX redirect somewhere better than just the front page...?
    auth_headers = security.forget(request)
    request.session.flash(u'Logged out.', icon='user-silhouette')
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
    request.auth.login_openid(user)
    request.session.save()

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
