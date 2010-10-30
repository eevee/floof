# -*- coding: utf-8 -*-
import logging
import re

from openid.consumer.consumer import Consumer
from openid.extensions.sreg import SRegRequest, SRegResponse
from openid.store.filestore import FileOpenIDStore
from openid.yadis.discover import DiscoveryFailure
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from routes import request_config
from sqlalchemy.orm.exc import NoResultFound
import wtforms.form, wtforms.fields, wtforms.validators

from floof.lib import helpers
from floof.lib.base import BaseController, render
from floof.model import IdentityURL, User, Role, meta

log = logging.getLogger(__name__)

class LoginForm(wtforms.form.Form):
    openid_identifier = wtforms.fields.TextField(u'OpenID URL')

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

class AccountController(BaseController):

    openid_store = FileOpenIDStore('/var/tmp')

    def login(self):
        c.form = LoginForm()
        return render('/account/login.mako')

    def login_begin(self):
        """Step one of logging in with OpenID; we redirect to the provider"""

        c.form = LoginForm(request.POST)
        if not c.form.validate():
            return render('/account/login.mako')

        cons = Consumer(session=session, store=self.openid_store)

        try:
            openid_url = c.form.openid_identifier.data
        except KeyError:
            c.form.openid_identifier.errors.append("Gotta enter an OpenID to log in.")
            return render('/account/login.mako')

        try:
            auth_request = cons.begin(openid_url)
        except DiscoveryFailure:
            c.form.openid_identifier.errors.append(
                "Can't connect to '{0}'.  You sure it's an OpenID?"
                .format(openid_url)
                )
            return render('/account/login.mako')

        sreg_req = SRegRequest(optional=['nickname', 'email', 'dob', 'gender',
                                         'country', 'language', 'timezone'])
        auth_request.addExtension(sreg_req)

        host = request.headers['host']
        protocol = request_config().protocol
        return_url = url(host=host, controller='account', action='login_finish')
        new_url = auth_request.redirectURL(return_to=return_url,
                                           realm=protocol + '://' + host)
        redirect(new_url)

    def login_finish(self):
        """Step two of logging in; the OpenID provider redirects back here."""

        cons = Consumer(session=session, store=self.openid_store)
        host = request.headers['host']
        return_url = url(host=host, controller='account', action='login_finish')
        res = cons.complete(request.params, return_url)

        if res.status != 'success':
            return 'Error!  %s' % res.message

        identity_url = unicode(res.identity_url)

        try:
            # Grab an existing user record, if one exists
            q = meta.Session.query(User) \
                    .filter(User.identity_urls.any(url=identity_url))
            user = q.one()

            # Remember who's logged in, and we're good to go
            session['user_id'] = user.id
            session.save()

            helpers.flash(u"""Hello, {0}!""".format(user.display_name),
                    icon='user')

            redirect(url('/'), code=303)

        except NoResultFound:
            # Nope.  Give a (brief!) registration form instead
            session['pending_identity_url'] = identity_url
            session.save()
            c.identity_url = identity_url

            # Try to pull a name out of the SReg response
            sreg_res = SRegResponse.fromSuccessResponse(res)
            try:
                username = sreg_res['nickname'].lower()
            except (KeyError, TypeError):
                # KeyError if sreg has no nickname; TypeError if sreg is None
                username = u''

            c.form = RegistrationForm(username=username)
            c.form.validate()
            return render('/account/register.mako')

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

        c.form = RegistrationForm(request.POST)
        if not c.form.validate():
            return render('/account/register.mako')

        # Create db records
        base_user = meta.Session.query(Role).filter_by(name=u'user').one()
        user = User(name=c.form.username.data, role=base_user)
        meta.Session.add(user)

        openid = IdentityURL(url=identity_url)
        user.identity_urls.append(openid)

        meta.Session.commit()

        # Log 'em in
        del session['pending_identity_url']
        session['user_id'] = user.id
        session.save()

        # And off we go
        redirect(url('/'), code=303)

    def logout(self):
        """Logs the user out."""

        if 'user_id' in session:
            del session['user_id']
            session.save()

            helpers.flash(u"""Logged out.""",
                    icon='user-silhouette')

        redirect(url('/'), code=303)
