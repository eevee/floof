# encoding: utf8
import logging
import re

from ssl import SSLError

from pyramid import security
from pyramid.httpexceptions import HTTPBadRequest, HTTPSeeOther
from pyramid.renderers import render_to_response
from pyramid.security import effective_principals
from pyramid.view import view_config
from sqlalchemy.exc import IntegrityError
from webhelpers.util import update_params

import vep.errors
import wtforms.form, wtforms.fields, wtforms.validators

from floof.forms import DisplayNameField, TimezoneField
from floof.lib.authn import DEFAULT_CONFIDENCE_EXPIRY
from floof.lib.authn import BrowserIDRemoteVerifier
from floof.lib.authn import BrowserIDAuthDisabledError, BrowserIDNotFoundError
from floof.lib.authn import OpenIDAuthDisabledError, OpenIDNotFoundError
from floof.lib.stash import fetch_stash, get_stash_keys, key_from_request
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
from floof.model import Discussion, IdentityURL, IdentityEmail, Resource
from floof.model import Role, User, UserProfileRevision
from floof import model

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
    # XXX worth mentioning on this page how to log in with SSL, and offer a
    # crypto link if they already hit cancel and want to try again

    # Auto-fill OpenID on re-auth
    return_key = key_from_request(request)
    openid = request.auth.openid_url if return_key else None

    # just_landed is imprecise, but should serve to reduce false positives
    just_landed = request.referrer is None
    just_landed = just_landed or (request.host not in request.referrer)
    if not request.cookies and not just_landed:
        request.session.flash(
                'It looks like you might not have cookies enabled in your '
                'browser.  Alas, cookies are required to log in.  If you '
                'think this message is in error, try refreshing the page.',
                icon='cookie--exclamation', level='warning')

    form = LoginForm(openid_identifier=openid, return_key=return_key)
    return {'form': form}


@view_config(
    route_name='account.browserid.login',
    request_method='POST',
    renderer='json')
def account_login_browserid(context, request):
    return_key = key_from_request(request)

    def fail(msg):
        request.session.flash(msg, level=u'error', icon='key--exclamation')
        # XXX setting the status to 403 triggers Pyramid's exception view
        #request.response.status = '403 Forbidden'
        next_url = request.route_url('account.login')
        if return_key is not None:
            next_url = update_params(next_url, return_key=return_key)
        return {'next_url': next_url}

    # Verify the identity assertion

    verifier = BrowserIDRemoteVerifier()
    audience = request.registry.settings.get('auth.browserid.audience')

    if not audience:
        log.warning("Config key 'auth.browserid.audience' is missing or "
                    "blank; BrowserID authentication will fail.")

    if 'paste.testing' in request.environ:
        alternative = request.environ.get('tests.auth.browserid.verifier')
        verifier = alternative or verifier

    try:
        data = verifier.verify(request.POST.get('assertion'), audience)

    except SSLError:
        return fail('Connection to authentication server failed or timed out.')

    except vep.errors.ConnectionError:
        return fail('Unable to connect to verifying server to verify your '
                    'BrowserID assertion.')

    except vep.errors.TrustError:
        return fail('Your BrowserID assertion was not valid.')

    except (vep.errors.Error, ValueError) as e:
        msg = e.args[0] if e.args else 'No error message'
        log.warning('Unspecified BrowserID failure: {0}'.format(msg))
        return fail('Encountered an unspecified error while attempting to '
                    'verify your BrowserID assertion.')

    print "BrowserID response:", data

    # Attempt to resolve the identity to a local user

    email = data.get('email')
    if data.get('status') != 'okay' or not email:
        return fail("BrowserID authentication failed.")

    identity_email = model.session.query(IdentityEmail) \
        .filter_by(email=email) \
        .limit(1).first()

    if not identity_email:
        # New user or new ID
        request.session['pending_identity_email'] = email
        return {'next_url': request.route_url('account.register'),
                'post_id': 'postform'}

    # Attempt to log in

    try:
        auth_headers = security.remember(
            request, identity_email.user, browserid_email=email)
        request.session.changed()

    except BrowserIDNotFoundError:
        return fail("The email address '{0}' is registered against the account "
                    "'{1}'.  To log in as '{1}', log out then back in."
                    .format(email, identity_email.user.name))

    except BrowserIDAuthDisabledError:
        return fail("Your BrowserID is no longer accepted as your account has "
                    "disabled BrowserID authentication.")

    # An existing user has logged in successfully.  Bravo!
    request.response.headerlist.extend(auth_headers)
    log.debug("User {0} logged in via BrowserID: {1}"
              .format(identity_email.user.name, identity_email))

    # Handle redirection

    if identity_email.user == request.user:
        # Someone is just freshening up their cookie
        request.session.flash(u'Re-authentication successful', icon='user')

        if return_key is not None:
            old_url = fetch_stash(request, key=return_key)['url']
            if old_url:
                next_url = update_params(old_url, return_key=return_key)
                log.debug('Following Return Key \'{0}\' to URL: {1}'
                          .format(return_key, next_url))
                return {'next_url': next_url}

        return {'next_url': request.route_url('root')}

    # Existing user; new login
    request.session.flash(
            'Logged in with BrowserID', level=u'success', icon='user')

    return {'next_url': request.route_url('root')}


@view_config(
    route_name='account.login_begin',
    request_method='POST',
    renderer='account/login.mako')
def login_begin(context, request):
    """Step one of logging in with OpenID; redirect to the provider."""
    form = LoginForm(request.POST)

    if not form.validate():
        return {'form': form}

    # Ensure the return key, if present and valid, will be passed
    # to openid_finish()
    return_url = request.route_url('account.login_finish')
    if form.return_key.data in get_stash_keys(request):
        return_url = update_params(return_url,
            return_key=form.return_key.data)

    if request.user:
        # Logged-in user trying to update their OpenID expiry time
        sreg = False
        settings = request.registry.settings
        max_auth_age = settings.get('auth.openid.expiry_seconds',
                                    DEFAULT_CONFIDENCE_EXPIRY)
    else:
        # Someone either logging in or registering
        # Problem is that we don't want sreg (as part of opeinid_begin) unless
        # the user is registering, but we don't know whether the user is
        # registering or just logging in until we resolve their identity URL...
        # which we do in openid_begin.
        # Possibly use checkid_immediate instead
        sreg = True
        max_auth_age = False

    try:
        return HTTPSeeOther(location=openid_begin(
                identifier=form.openid_identifier.data,
                return_url=return_url,
                request=request,
                max_auth_age=max_auth_age,
                sreg=sreg))

    except OpenIDError as exc:
        request.session.flash(exc.message,
            level='error', icon='key--exclamation')
        return {'form': form}


def safe_openid_login(request, identity_owner, identity_url):
    """Helper function, catches any exceptions that may be raised on OpenID
    login."""
    try:
        auth_headers = security.remember(
            request, identity_owner, openid_url=identity_url)
    except OpenIDAuthDisabledError:
        request.session.flash("Your OpenID is no longer accepted as your "
            "account has disabled OpenID authentication.",
            level='error', icon='key--exclamation')
    except OpenIDNotFoundError:
        request.session.flash("I don't recognize your OpenID identity.",
            level='error', icon='key--exclamation')
    else:
        return auth_headers


@view_config(
    route_name='account.login_finish',
    request_method='GET')
def login_finish(context, request):
    """Step two of logging in; the OpenID provider redirects back here."""

    def retry():
        """Redirect to the login page, preserving the return key (if any)."""
        location = request.route_url('account.login')
        if return_key:
            location = update_params(location, return_key=return_key)
        return HTTPSeeOther(location=location)

    return_url = request.route_url('account.login_finish')

    return_key = key_from_request(request)
    if return_key is not None:
        return_url = update_params(return_url, return_key=return_key)

    try:
        identity_url, identity_webfinger, auth_time, sreg_res = openid_end(
            return_url=return_url,
            request=request)
    except OpenIDError as exc:
        request.session.flash(exc.message,
            level='error', icon='key--exclamation')
        return retry()

    # Find who owns this URL, if anyone
    identity_owner = model.session.query(User) \
        .filter(User.identity_urls.any(url=identity_url)) \
        .limit(1).first()

    if not identity_owner:
        if return_key:
            request.session.flash('Unknown OpenID URL.',
                level='error', icon='key--exclamation')
            return retry()
        # Someone is either registering a new account, or adding a new OpenID
        # to an existing account
        request.session['pending_identity_url'] = identity_url
        request.session.changed()

        # Try to pull a name and email address out of the SReg response
        username = re.sub(u'[^_a-z0-9]', u'',
            sreg_res.get('nickname', u'').lower())
        form = RegistrationForm(
            username=username,
            email=sreg_res.get('email', u''),
            timezone=sreg_res.get('timezone', u'UTC'),
        )
        return render_to_response(
            'account/register.mako',
            dict(
                form=form,
                identity_url=identity_url,
                identity_webfinger=identity_webfinger),
            request=request)

    elif identity_owner == request.user:
        # Someone is just freshening up their cookie
        auth_headers = safe_openid_login(request, identity_owner, identity_url)
        if auth_headers is None:
            return retry()

        request.session.flash(u'Re-authentication successful', icon='user')

        if return_key:
            # Fetch a stashed request
            old_url = fetch_stash(request, key=return_key)['url']
            if old_url:
                location = update_params(old_url, return_key=return_key)
                log.debug('Following Return Key \'{0}\' to URL: {1}'
                          .format(return_key, location))
                return HTTPSeeOther(location, headers=auth_headers)
        return HTTPSeeOther(request.route_url('root'), headers=auth_headers)

    else:
        # Existing user; new login
        # Log the successful OpenID authentication, mindful of users that may
        # have OpenID logins disabled, for instance.
        # XXX should we deny a logged-in user to authenticate as another user?
        auth_headers = security.forget(request)
        headers = safe_openid_login(request, identity_owner, identity_url)

        if headers is None:
            return retry()

        auth_headers += headers

        # An existing user has logged in successfully.  Bravo!
        log.debug("User {0!r} logged in via OpenID: {1!r}"
                  .format(identity_owner.name, identity_url))

        request.session.flash(
            u"Welcome back, {0}!"
            .format(identity_owner.display_name or identity_owner.name),
            level=u'success', icon='user')

        # XXX this should ALSO probably do the return_key redirect, good grief
        return HTTPSeeOther(
            location=request.route_url('root'),
            headers=auth_headers)


@view_config(
    route_name='account.logout',
    request_method='POST')
def logout(context, request):
    """Logs the user out, if possible."""

    cert_active = 'trusted:cert' in effective_principals(request)

    # XXX if you're using a client cert, this should try hard to log you out
    # with the crypto api
    # XXX redirect somewhere better than just the front page...?
    auth_headers = security.forget(request)
    request.session.invalidate()  # Prevent the next user seeing this session

    if cert_active:
        request.session.flash(u'You must stop sending your client certificate '
                              'to complete your log out.', level='warning')
    else:
        request.session.flash(u'Logged out.', icon='user-silhouette')

    return HTTPSeeOther(
        location=request.route_url('root'),
        headers=auth_headers,
    )


class RegistrationForm(wtforms.form.Form):
    # XXX steal the validation and max len from =>
    display_name = DisplayNameField(u'Display name')

    # XXX come on, man; make this thing lowercase yourself
    username = wtforms.fields.TextField(u'Username', [
        wtforms.validators.Regexp(r'^[_a-z0-9]{1,24}$',
            message=u'Your username must be 1–24 characters and contain only '
            u'lowercase letters, numbers, and underscores.'
            ),
        ])
    email = wtforms.fields.TextField(u'Email address', [
            wtforms.validators.Optional(),
            wtforms.validators.Email(
                message=u'That does not appear to be an email address.'),
            ])
    timezone = TimezoneField(u'Timezone')

    def validate_username(form, field):
        if model.session.query(User).filter_by(name=field.data).count():
            raise wtforms.validators.ValidationError(
                'Your username is already taken. Please try again.')


@view_config(
    route_name='account.register',
    request_method='POST')
def register(context, request):
    def clear_pending():
        request.session.pop('pending_identity_email', None)
        request.session.pop('pending_identity_url', None)
        request.session.pop('pending_identity_webfinger', None)

    def bail():
        # Abort registration; typically if the request is nonsensical
        clear_pending()
        request.session.flash('Your session expired.  Please try logging in again.')
        return HTTPSeeOther(location=request.route_url('account.login'))

    # Check identity URL

    identity_url = request.session.get('pending_identity_url')
    identity_email = request.session.get('pending_identity_email')
    openid_q = model.session.query(IdentityURL).filter_by(url=identity_url)
    browserid_q = model.session.query(IdentityEmail).filter_by(email=identity_email)

    # Must register against (or add) exactly one ID
    if not identity_url and not identity_email:
        return bail()
    if identity_url and identity_email:
        return bail()

    # Cannot re-register an ID
    if identity_url and openid_q.count():
        return bail()
    if identity_email and browserid_q.count():
        return bail()

    # display_only for use with BrowserID since it can only redirect or POST,
    # not display a page directly (because it's all AJAX).
    display_only = request.params.get('display_only')
    if display_only:
        form = RegistrationForm(email=identity_email)
    else:
        form = RegistrationForm(request.POST)

    if display_only or not form.validate():
        return render_to_response('account/register.mako', {
                'form': form,
                'identity_email': identity_email,
                'identity_url': identity_url,
                'identity_webfinger': request.session.get('pending_identity_webfinger'),
            },
            request=request)

    # XXX waiting on auth_dev2 branch to merge to factor this out of controls
    from floof.lib.helpers import reduce_display_name
    if not form.display_name.data:
        display_name = None
        has_trivial_display_name = False
    else:
        display_name = form.display_name.data
        has_trivial_display_name = (form.username.data ==
            reduce_display_name(display_name))

    # Create db records
    resource = Resource(type=u'users')
    discussion = Discussion(resource=resource)
    user = User(
        name=form.username.data,
        email=form.email.data,
        resource=resource,
        timezone=form.timezone.data,

        display_name=display_name,
        has_trivial_display_name=has_trivial_display_name,
    )
    model.session.add_all((user, resource, discussion))

    base_user = model.session.query(Role).filter_by(name=u'user').one()
    user.roles.append(base_user)

    if identity_url:
        openid = IdentityURL(url=identity_url)
        user.identity_urls.append(openid)
    else:
        browserid = IdentityEmail(email=identity_email)
        user.identity_emails.append(browserid)

    model.session.flush()

    log.info('User #{0} registered: {1}'.format(user.id, user.name))

    # Log 'em in
    clear_pending()
    auth_headers = security.forget(request)
    headers = security.remember(
            request, user, openid_url=identity_url,
            browserid_email=identity_email)
    if headers is None:
        log.error("Failed to log in new registrant.")  # shouldn't happen
    else:
        auth_headers += headers

    # And off we go
    return HTTPSeeOther(request.route_url('root'), headers=auth_headers)


@view_config(
    route_name='account.add_identity',
    permission='auth.openid',
    request_method='POST')
def add_identity(context, request):
    identity_url = request.session.pop('pending_identity_url', None)
    identity_email = request.session.pop('pending_identity_email', None)
    request.session.save()

    # Sanity checks; neither case should happen
    if not identity_url and not identity_email:
        return HTTPBadRequest()
    if identity_url and identity_email:
        return HTTPBadRequest()

    if identity_url:
        model.session.add(
            IdentityURL(user=request.user, url=identity_url))
    else:
        model.session.add(
            IdentityEmail(user=request.user, email=identity_email))

    try:
        model.session.flush()
    except IntegrityError:
        # Somehow you're trying to add an already-claimed identity.  This
        # shouldn't happen either
        return HTTPBadRequest()

    request.session.flash(
        u"Added a new identity: {0}".format(identity_url or identity_email),
        level=u'success', icon=u'user--plus')
    dest = 'controls.openid' if identity_url else 'controls.browserid'
    return HTTPSeeOther(location=request.route_url(dest))


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
        rev = UserProfileRevision(user=request.user, updated_by=request.user,
                                  content=profile)
        model.session.add(rev)

    return {}
