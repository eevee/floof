# encoding: utf8
import logging
import re

from pyramid import security
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from webhelpers.util import update_params
import wtforms.form, wtforms.fields, wtforms.validators

from floof.forms import DisplayNameField, TimezoneField
from floof.lib.stash import fetch_stash, get_stash_keys, key_from_request
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
from floof.model import Resource, Discussion, UserProfileRevision, IdentityURL, User, Role
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
    form = LoginForm()
    # XXX worth mentioning on this page how to log in with SSL, and offer a
    # crypto link if they already hit cancel and want to try again
    # XXX why do we need this?: form.openid_identifier.data = request.auth.openid_url
    # ^^^ that was to pre-fill the form in the (maybe) common case of re-auth
    form.return_key.data = key_from_request(request)
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
    if form.return_key.data in get_stash_keys(request):
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
        request.session.flash(exc.message,
            level='error', icon='key--exclamation')
        return render_to_response(
            'account/login.mako', {'form': form}, request=request)


@view_config(
    route_name='account.login_finish',
    request_method='GET')
def login_finish(context, request):
    """Step two of logging in; the OpenID provider redirects back here."""
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

        location = request.route_url('account.login')
        if return_key:
            location = update_params(location, return_key=return_key)

        return HTTPSeeOther(location=location)

    # Find who owns this URL, if anyone
    identity_owner = model.session.query(User) \
        .filter(User.identity_urls.any(url=identity_url)) \
        .limit(1).first()

    if not identity_owner:
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
        request.auth.login_openid(identity_owner, identity_url)
        request.session.changed()
        request.session.flash(u'Re-authentication successful', icon='user')

        if return_key:
            # Fetch a stashed POST request
            old_url = fetch_stash(request, return_key)['url']
            if old_url:
                location = update_params(old_url, return_key=return_key)
                log.debug('Following Return Key \'{0}\' to URL: {1}' \
                    .format(return_key, location))
                return HTTPSeeOther(location)

        return HTTPSeeOther(location=request.route_url('root'))

    else:
        # An existing user has logged in successfully.  Bravo!
        log.debug("User {0!r} logged in via OpenID: {1!r}".format(identity_owner.name, identity_url))

        # Log the successful authentication
        # TODO try/except, catch all the things that can be thrown
        auth_headers = security.forget(request)
        auth_headers += security.remember(
            request, identity_owner, openid_url=identity_url)
        request.session.flash(
            u"Welcome back, {0}!".format(identity_owner.display_name or identity_owner.name),
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
            wtforms.validators.Email(message=u'That does not appear to be an email address.'),
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
    # Check identity URL
    identity_url = request.session.get('pending_identity_url')
    if not identity_url or \
       model.session.query(IdentityURL) \
            .filter_by(url=identity_url).count():

        # Not in the session or is already registered.  Neither makes
        # sense.  Bail.
        helpers.flash('Your session expired.  Please try logging in again.')
        return HTTPSeeOther(location=request.route_url('account.login'))

    form = RegistrationForm(request.POST)
    if not form.validate():
        return render_to_response('account/register.mako', {
                'form': form,
                'identity_url': identity_url,
                'identity_webfinger': request.session.get('pending_identity_webfinger'),
            },
            request=request)

    # XXX waiting on auth_dev2 branch to merge to factor this out of controls
    from floof.views.controls import reduce_display_name
    if not form.display_name.data:
        display_name = None
        has_trivial_display_name = False
    else:
        display_name = form.display_name.data
        has_trivial_display_name = (form.username.data ==
            reduce_display_name(display_name))

    # Create db records
    base_user = model.session.query(Role).filter_by(name=u'user').one()
    resource = Resource(type=u'users')
    discussion = Discussion(resource=resource)
    user = User(
        name=form.username.data,
        email=form.email.data,
        role=base_user,
        resource=resource,
        timezone=form.timezone.data,

        display_name=display_name,
        has_trivial_display_name=has_trivial_display_name,
    )
    model.session.add_all((user, resource, discussion))

    openid = IdentityURL(url=identity_url)
    user.identity_urls.append(openid)

    model.session.flush()

    log.info('User #{0} registered: {1}'.format(user.id, user.name))

    # Log 'em in
    del request.session['pending_identity_url']
    auth_headers = security.forget(request)
    auth_headers += security.remember(request, user, openid_url=identity_url)
    print auth_headers

    # And off we go
    return HTTPSeeOther(
        location=request.route_url('root'),
        headers=auth_headers)


@view_config(
    route_name='account.add_identity',
    permission='__authenticated__',
    request_method='POST')
def add_identity(context, request):
    identity_url = request.session.pop('pending_identity_url', None)
    request.session.save()

    if not identity_url:
        # You shouldn't be here
        return HTTPBadRequest()

    model.session.add(IdentityURL(user=request.user, url=identity_url))

    try:
        model.session.flush()
    except IntegrityError:
        # Somehow you're trying to add an already-claimed URL.  This shouldn't
        # happen either
        return HTTPBadRequest()

    request.session.flash(
        u"Added a new identity: {0}".format(identity_url),
        level=u'success', icon=u'user--plus')
    return HTTPSeeOther(location=request.route_url('controls.openid'))


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
        model.session.add(rev)

    return {}
