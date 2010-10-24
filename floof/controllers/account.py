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

from floof.lib import helpers as h
from floof.lib.base import BaseController, render
from floof.model import IdentityURL, User, meta

log = logging.getLogger(__name__)

class AccountController(BaseController):

    openid_store = FileOpenIDStore('/var/tmp')

    def _username_error(self, username):
        """Check whether the username is valid and taken.

        Returns a short error string, or None if it's fine.
        """

        if not username:
            return 'missing'
        elif not re.match('^[_a-z0-9]{1,24}$', username):
            return 'invalid'
        elif meta.Session.query(User).filter_by(name=username).count():
            return 'taken'
        else:
            return None

    def _bail(self, reason):
        # Used for bailing on a login attempt; reshows the login page
        c.error = reason
        c.attempted_openid = request.params.get('openid_identifier', '')
        return render('/account/login.mako')


    def login(self):
        c.error = None
        c.attempted_openid = None
        return render('/account/login.mako')

    def login_begin(self):
        """Step one of logging in with OpenID; we redirect to the provider"""

        cons = Consumer(session=session, store=self.openid_store)

        try:
            openid_url = request.params['openid_identifier']
        except KeyError:
            return self._bail("Gotta enter an OpenID to log in.")

        try:
            auth_request = cons.begin(openid_url)
        except DiscoveryFailure:
            return self._bail(
                "Can't connect to '{0}'.  You sure it's an OpenID?"
                .format(openid_url)
            )

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

            h.flash(u"""Hello, {0}!""".format(user.display_name),
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
                c.username = sreg_res['nickname'].lower()
            except (KeyError, TypeError):
                # KeyError if sreg has no nickname; TypeError if sreg is None
                c.username = u''

            c.username_error = self._username_error(c.username)

            return render('/account/register.mako')

    def register(self):
        # Check identity URL
        identity_url = session.get('pending_identity_url', None)
        if not identity_url or \
           meta.Session.query(IdentityURL) \
                .filter_by(url=identity_url).count():

            # Not in the session or is already registered.  Neither makes
            # sense.  Bail.
            h.flash('Your session expired.  Please try logging in again.')
            redirect(url(controller='account', action='login'), code=303)

        # Check username
        username = request.params.get('username', None)
        c.username_error = self._username_error(username)
        print c.username_error

        if c.username_error:
            # Somethin wrong!  Make 'em try again
            c.username = username
            c.identity_url = identity_url
            return render('/account/register.mako')

        # Create db records
        user = User(name=username)
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

            h.flash(u"""Logged out.""",
                    icon='user-silhouette')

        redirect(url('/'), code=303)
