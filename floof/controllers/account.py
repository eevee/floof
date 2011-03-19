# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import pytz
import re

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort
from sqlalchemy.orm.exc import NoResultFound
from urllib2 import HTTPError, URLError
import wtforms.form, wtforms.fields, wtforms.validators

from floof.lib import helpers
from floof.lib.auth import CERT_CONFIDENCE_EXPIRY_SECONDS, CONFIDENCE_EXPIRY_SECONDS, fetch_stash_url, stash_keys
from floof.lib.base import BaseController, render
from floof.lib.decorators import logged_in, logged_out
from floof.lib.helpers import redirect
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
from floof import model
from floof.model import Discussion, UserProfileRevision, IdentityURL, User, Role, meta

log = logging.getLogger(__name__)

def gen_timezone_choices():
    #XXX: Perfect for caching; the list is unlikely to change more than hourly.
    tzs = []
    now = datetime.now()
    for tz_name in pytz.common_timezones:
        offset = pytz.timezone(tz_name).utcoffset(now)
        offset_real_secs = offset.seconds + offset.days * 24 * 60**2
        offset_hours, remainder = divmod(offset_real_secs, 3600)
        offset_minutes, _ = divmod(remainder, 60)
        offset_txt = '(UTC {0:0=+3d}:{1:0>2d}) {2}'.format(
                offset_hours, offset_minutes, tz_name)
        tzs.append((offset_real_secs, tz_name, offset_txt))
    tzs.sort()
    return [tz[1:] for tz in tzs]

class LoginForm(wtforms.form.Form):
    # n.b.: This is actually a name recommended by the OpenID spec, for ease of
    # client identification
    openid_identifier = wtforms.fields.TextField(u'OpenID URL or Webfinger-enabled email address',
            validators=[wtforms.validators.Required(u'Gotta enter an OpenID to log in.')]
            )
    return_key = wtforms.fields.HiddenField(u'Return Stash Key')

class RegistrationForm(wtforms.form.Form):
    username = wtforms.fields.TextField(u'Username', [
        wtforms.validators.Regexp(r'^[_a-z0-9]{1,24}$',
            message=u'Your username must be 1–24 characters and contain only '
            u'lowercase letters, numbers, and underscores.'
            ),
        ])
    timezone = wtforms.fields.SelectField(u'Timezone',
            choices=gen_timezone_choices(),
            )

    def validate_username(form, field):
        if meta.Session.query(User).filter_by(name=field.data).count():
            raise wtforms.validators.ValidationError(
                'Your username is already taken. Please try again.')

class ProfileForm(wtforms.form.Form):
    profile = wtforms.fields.TextField(u'Profile')

class AccountController(BaseController):

    def login(self):
        c.form = LoginForm()
        c.form.openid_identifier.data = c.auth.openid_url
        c.form.return_key.data = request.GET.get('return_key', None)
        return render('/account/login.mako')

    def login_begin(self):
        """Step one of logging in with OpenID; redirect to the provider."""
        c.form = LoginForm(request.POST)

        if not c.form.validate():
            return render('/account/login.mako')

        # Ensure the return key, if present and valid, will be passed
        # to openid_finish()
        if c.form.return_key.data in stash_keys(session):
            return_url=url(host=request.headers['host'],
                    controller='account',
                    action='login_finish',
                    return_key=c.form.return_key.data,
                    )
        else:
            return_url=url(host=request.headers['host'],
                    controller='account',
                    action='login_finish',
                    )

        if c.user:
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
            redirect(openid_begin(
                    identifier=c.form.openid_identifier.data,
                    return_url=return_url,
                    max_auth_age=max_auth_age,
                    sreg=sreg,
                    ))
        except OpenIDError as exc:
            c.form.openid_identifier.errors.append(exc.args[0])
            return render('/account/login.mako')

    def login_finish(self):
        """Step two of logging in; the OpenID provider redirects back here."""
        return_key = request.GET.get('return_key', None)
        if return_key:
            if return_key not in stash_keys(session):
                abort(400, detail='Unknown return_key value')
            return_url=url(host=request.headers['host'],
                    controller='account',
                    action='login_finish',
                    return_key=return_key,
                    )
        else:
            return_url=url(host=request.headers['host'],
                    controller='account',
                    action='login_finish',
                    )

        try:
            identity_url, identity_webfinger, auth_time, sreg_res = openid_end(
                    return_url=return_url,
                    )
        except OpenIDError as exc:
            return exc.args[0]

        if c.user:
            # An existing user is trying to re-auth
            if c.auth.openid_success(session, c.user.id, identity_url, auth_time):
                helpers.flash(u'Re-authentication successful', icon='user')
                if return_key:
                    # Fetch a stashed POST request
                    old_url = fetch_stash_url(session, return_key)
                    if old_url:
                        log.debug('Following Return Key \'{0}\' to URL: {1}' \
                                .format(return_key, old_url))
                        redirect('{0}?return_key={1}'.format(old_url, return_key))
                redirect(url('/'))
            helpers.flash(u'Re-authentication unsuccessful.  Was \'{0}\' a '
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

            log.debug('User {0} (#{1}) authenticated with OpenID URL "{2}"'
                    .format(user.id, user.name, identity_url))

            # Log the successful authentication
            if c.auth.openid_success(session, user.id, identity_url):
                helpers.flash(u'Hello, {0}'.format(user.display_name),
                        icon='user')
                redirect(url('/'))
            redirect(url(controller='account', action='login'))

        except NoResultFound:
            # Nope.  Give a (brief!) registration form instead
            session['pending_identity_url'] = identity_url
            session.save()
            c.identity_url = identity_url
            c.identity_webfinger = session.get('pending_identity_webfinger', None)

            # Try to pull a name and email addraess out of the SReg response
            c.form = RegistrationForm(
                    username=sreg_res.get('nickname', u''),
                    timezone=sreg_res.get('timezone', 'UTC'),
                    )
            c.form.validate()
            return render('/account/register.mako')

    @logged_out
    def register(self):
        # Check identity URL
        identity_url = c.identity_url = session.get('pending_identity_url')
        if not identity_url or \
           meta.Session.query(IdentityURL) \
                .filter_by(url=identity_url).count():

            # Not in the session or is already registered.  Neither makes
            # sense.  Bail.
            helpers.flash('Your session expired.  Please try logging in again.')
            redirect(url(controller='account', action='login'))

        c.identity_webfinger = session.get('pending_identity_webfinger', None)
        c.form = RegistrationForm(request.POST)
        if not c.form.validate():
            return render('/account/register.mako')

        # Create db records
        base_user = meta.Session.query(Role).filter_by(name=u'user').one()
        resource = model.Resource(type=u'users')
        discussion = model.Discussion(resource=resource)
        user = User(
            name=c.form.username.data,
            role=base_user,
            resource=resource,
            timezone=pytz.timezone(c.form.timezone.data),
        )
        meta.Session.add_all([user, resource, discussion])

        openid = IdentityURL(url=identity_url)
        user.identity_urls.append(openid)

        meta.Session.commit()
        log.info('User #{0} registered: {1}'.format(user.id, user.name))

        # Log 'em in
        del session['pending_identity_url']
        c.auth.openid_success(session, user.id, identity_url)

        # And off we go
        redirect(url('/'))

    def logout(self):
        """Logs the user out, if possible."""

        if c.auth.can_purge:
            c.auth.purge(session)
            helpers.flash(u'Logged out.',
                  icon='user-silhouette')
        redirect(url('/'))

    @logged_in
    def profile(self):
        c.form = ProfileForm(request.POST)

        if request.method == 'POST' and c.form.validate():
            profile = c.form.profile.data
            c.user.profile = profile
            rev = UserProfileRevision(user=c.user, updated_by=c.user, content=profile)
            meta.Session.add(rev)
            meta.Session.commit()
        else:
            return render('/account/profile.mako')
