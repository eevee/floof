# -*- coding: utf-8 -*-
import logging
import re

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from sqlalchemy.orm.exc import NoResultFound
from urllib2 import HTTPError, URLError
import wtforms.form, wtforms.fields, wtforms.validators

from floof.lib import auth, helpers
from floof.lib.base import BaseController, render
from floof.lib.decorators import logged_in, logged_out
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
from floof import model
from floof.model import Discussion, UserProfileRevision, IdentityURL, User, Role, meta

log = logging.getLogger(__name__)

class LoginForm(wtforms.form.Form):
    # n.b.: This is actually a name recommended by the OpenID spec, for ease of
    # client identification
    openid_identifier = wtforms.fields.TextField(u'OpenID URL or Webfinger-enabled email address',
            validators=[wtforms.validators.Required(u'Gotta enter an OpenID to log in.')]
            )

class RegistrationForm(wtforms.form.Form):
    username = wtforms.fields.TextField(u'Username', [
        wtforms.validators.Regexp(r'^[_a-z0-9]{1,24}$',
            message=u'Your username must be 1–24 characters and contain only '
            u'lowercase letters, numbers, and underscores.'
            ),
        ])

    def validate_username(form, field):
        if meta.Session.query(User).filter_by(name=field.data).count():
            raise wtforms.validators.ValidationError(
                'Your username is already taken. Please try again.')

class ProfileForm(wtforms.form.Form):
    profile = wtforms.fields.TextField(u'Profile')

class AccountController(BaseController):

    @logged_out
    def login(self):
        c.form = LoginForm()
        return render('/account/login.mako')

    @logged_out
    def login_begin(self):
        """Step one of logging in with OpenID; redirect to the provider."""
        c.form = LoginForm(request.POST)

        if 'openid' in c.auth.satisfied_mechanisms:
            redirect(url(controller='account', action='login'), code=303)
        if not c.form.validate():
            return render('/account/login.mako')

        try:
            redirect(openid_begin(
                    identifier=c.form.openid_identifier.data,
                    return_url=url(host=request.headers['host'],
                        controller='account',
                        action='login_finish',
                        )
                    ), code=303)
        except OpenIDError as exc:
            c.form.openid_identifier.errors.append(exc.args[0])
            return render('/account/login.mako')

    @logged_out
    def login_finish(self):
        """Step two of logging in; the OpenID provider redirects back here."""

        try:
            identity_url, identity_webfinger, sreg_res = openid_end(
                    return_url=url(host=request.headers['host'],
                        controller='account',
                        action='login_finish',
                    ))
        except OpenIDError as exc:
            return exc.args[0]

        try:
            # Grab an existing user record, if one exists
            q = meta.Session.query(User) \
                    .filter(User.identity_urls.any(url=identity_url))
            user = q.one()

            log.debug('User {0} (#{1}) authenticated with OpenID URL "{2}"'
                    .format(user.id, user.name, identity_url)) 

            # Log the successful authentication
            if c.auth.auth_success(session, 'openid', user.id):
                redirect(url('/'), code=303)
            redirect(url(controller='account', action='login'), code=303)

        except NoResultFound:
            # Nope.  Give a (brief!) registration form instead
            session['pending_identity_url'] = identity_url
            session.save()
            c.identity_url = identity_url
            c.identity_webfinger = session.get('pending_identity_webfinger', None)

            # Try to pull a name out of the SReg response
            try:
                username = sreg_res['nickname'].lower()
            except (KeyError, TypeError):
                # KeyError if sreg has no nickname; TypeError if sreg is None
                username = u''

            c.form = RegistrationForm(username=username)
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
            redirect(url(controller='account', action='login'), code=303)

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
        )
        meta.Session.add_all([user, resource, discussion])

        openid = IdentityURL(url=identity_url)
        user.identity_urls.append(openid)

        meta.Session.commit()
        log.info('User #{0} registered: {1}'.format(user.id, user.name))

        # Log 'em in
        del session['pending_identity_url']
        c.auth.auth_success(session, 'openid', user.id)

        # And off we go
        redirect(url('/'), code=303)

    @logged_in
    def logout(self):
        """Logs the user out, if possible."""

        if c.auth.can_purge:
            c.auth.purge(session)
            helpers.flash(u'Logged out.',
                  icon='user-silhouette')
        redirect(url('/'), code=303)

    def purge_auth(self):
        c.auth.purge(session)
        helpers.flash(u'Authentication data purged.',
                icon='user-silhouette')
        redirect(url(controller='account', action='login'), code=303)

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
