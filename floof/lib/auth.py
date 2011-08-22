from pylons import config, request
from pylons.controllers.util import abort

import OpenSSL.crypto as ssl
from pyramid.decorator import reify
from pyramid.security import ACLAllowed, ACLDenied
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from floof import model
from floof.model import meta, Certificate

import calendar
from datetime import datetime, timedelta
import os
import random
import time

persistant_variables = [
        'openid_uid',
        'openid_url',
        'openid_time',
        'cert_uid',
        'cert_serial',
        ]

req_confidence_levels = {
        1: ['auth', 'money'],
        2: ['admin']
        }

CONFIDENCE_EXPIRY_SECONDS = int(config.get('auth_confidence_expiry_seconds', 60 * 10))
CERT_CONFIDENCE_EXPIRY_SECONDS = int(config.get('cert_auth_confidence_expiry_seconds', 60 * 30))

sensitive_privs = []
for lvl in req_confidence_levels:
    for priv in req_confidence_levels[lvl]:
        sensitive_privs.append(priv)

class FloofAuthnPolicy(object):
    """Authentication policy bolted atop a beaker session.

    Most of the actual work here is done by the Auth class below.  The Pyramid
    auth interface is extremely clunky, and this class only exists so standard
    Pyramid authorization stuff still works.
    """

    def authenticated_userid(self, request):
        raise NotImplementedError()

    def unauthenticated_userid(self, request):
        raise NotImplementedError()

    def effective_principals(self, request):
        # XXX this basically spits on Pyramid's entire ACL thing
        # XXX an ACL would be useful for multiple roles, where e.g. "user" has
        # a bunch of permissions but "banned" removes them all
        user = request.user
        if user:
            privs = set(priv.name for priv in user.role.privileges)

            # TODO make these, like, pseudoroles, and replace them in code with
            # actual privs
            privs.add('__authenticated__')
            # TODO the whole idea of 'levels' can kinda go away here I guess
            if request.auth.trusted >= 1:
                privs.add('trusted:recent')  # XXX make your mind up on syntax
                # XXX additionally that's a bad name since 'cert' includes 'recent'
            if request.auth.trusted >= 2:
                privs.add('trusted:cert')

            return privs

        else:
            return []

    def remember(self, request, principal, **kw):
        request.auth.login_openid(principal)
        request.session.save()

    def forget(self, request):
        request.session.pop('auth', None)

class FloofAuthzPolicy(object):
    """Authorization policy that uses simple permissions stored in the db."""

    def permits(self, context, principals, permission):
        # XXX should these return Allowed/Denied too?

        # XXX this basically spits on Pyramid's whole ACL thing.
        # XXX a later thought: the role_privileges table IS the ACL, and we're
        # kind of short-circuiting it here
        if permission not in principals:
            return ACLDenied('<default deny>', principals, permission, principals, context)

        # TODO this stuff should be in the db as properties of the Privilege.
        # alternatively, scrap the db and keep this stuff in code, since having
        # roles in the db should already be plenty flexible.
        addl_permission = None
        if permission.startswith('auth.'):
            addl_permission = 'trusted:recent'
        elif permission.startswith('admin.'):
            addl_permission = 'trusted:cert'
        # XXX what about sensitive_required, ugh

        # XXX this is stupid.  move it to a decorator or something on the actual view code.
        if 0 and addl_permission and addl_permission not in principals:
            # XXX preserve the messages from the deocorators
            # XXX also, fix the user-facing error pages in general good lord
            return ACLDenied('<addl default deny>', principals, addl_permission, principals, context)

        return ACLAllowed('<woohoo>', principals, permission, principals, context)


class CertNotFoundError(Exception): pass
class CertAuthDisabledError(Exception): pass
class CertRevokedError(Exception): pass
class OpenIDAuthDisabledError(Exception): pass
class CertAuthConflictError(Exception): pass

class Authenticizer(object):
    """Manages the authentication and authorization state of the current user.

    This class is intended to be instantiated from a Request object.  The authn
    and authz policy classes above expect to find an instance of this class on
    the request, and delegate Pyramid security functionality here.

    State is contained within a dictionary, passed to the constructor.
    """
    def __init__(self, request):
        # The point of this whole method is really just to get a user id.
        # Note: everything within the state is meant to be consistent at all
        # times; i.e., there should never be a cert serial, openid, or user id
        # that don't all match.
        self.state = request.session.setdefault('auth', {})
        mechanisms = []

        # Test amenity
        if 'tests.user_id' in request.environ:
            # Override user id manually
            self.state.clear()
            self.state['user_id'] = request.environ['tests.user_id']
            self.confidence = 2  # maximum!
            request.session.changed()
            return
        # If testing, override mechanism states as requested
        # XXX uhh support these I guess maybe.
        #for var in persistant_variables:
        #    if 'tests.auth_{0}'.format(var) in request.environ:
        #        setattr(self, var, request.environ['tests.auth_{0}'.format(var)])

        # Check for client certificate login; the cert serial is passed by the
        # frontend server in an HTTP header.  This effectively acts as a login
        # if it changes
        # XXX thinking the secret stuff should become a general "don't be world-readable"
        try:
            cert_serial = request.environ['tests.auth_cert_serial']
        except KeyError:
            try:
                cert_serial = request.headers['X-Floof-SSL-Client-Serial']
            except KeyError:
                cert_serial = None

        try:
            self.login_certificate(cert_serial)
        except CertNotFoundError:
            # This should NEVER happen in production (certs should last
            # forever)
            request.session.flash("I don't recognize your client certificate.",
                level='error', icon='key--exclamation')
        except CertAuthDisabledError:
            request.session.flash("Client certificates are disabled for your account.",
                level='error', icon='key--exclamation')
        except CertRevokedError:
            request.session.flash("That client certificate has been revoked.",
                level='error', icon='key--exclamation')

        # Check confidence level.
        # Guests are -1.
        # A regular OpenID login is 0 (standard).
        # If performed fairly recently, it's 1 (semi-trusted).
        # Client certificates are 2 (trusted).
        # XXX check for cert_auth and remove disabled mechanisms separately, with a warning to the user or something
        self.trusted = -1
        if not self.user:
            pass
        elif 'cert_serial' in self.state and self.user.cert_auth != u'disabled':
            self.trusted = 2
        elif 'openid_timestamp' in self.state and self.user.cert_auth != u'required':
            age = datetime.now() - datetime.fromtimestamp(self.state['openid_timestamp'])
            if age <= timedelta(seconds=CONFIDENCE_EXPIRY_SECONDS) and self.user.cert_auth != u'sensitive_required':
                self.trusted = 1
            else:
                self.trusted = 0

        if self.trusted == -1:
            # Either there's no user, or none of their current auths are valid.
            # Wipe the slate clean
            self.state.clear()
            del self.user

        print self.state
        request.session.changed()

    def login_certificate(self, serial):
        """Log in via client certificate serial.

        `serial` may be `None`, in which case no actual login is done, but
        existing cert-related state is cleared.
        """
        if serial:
            serial = serial.lower()

        # Certificates are sent on every request.  To avoid db churn looking
        # them up constantly, the last seen serial is saved in the session
        if serial == self.state.get('cert_serial', None):
            # Stored serial matches the new one (even if the new one is None),
            # so the state's user_id is correct and there's nothing to do
            return
            # XXX surely we should check whether the cert was revoked in the
            # meantime

        if not serial:
            # No cert given, but we had one before.  Clear the serial from the
            # state.  If this was the only login mechanism the user had,
            # __init__ will wipe out user_id too
            self.state.pop('cert_serial', None)
            return

        # OK, figure out what certificate and user this serial belongs to
        cert_q = meta.Session.query(model.Certificate) \
            .options(joinedload(model.Certificate.user)) \
            .filter_by(serial=serial)

        try:
            cert = cert_q.one()
        except NoResultFound:
            raise CertNotFoundError

        if cert.user.cert_auth == u'disabled':
            raise CertAuthDisabledError
        if cert.revoked:
            raise CertRevokedError

        if cert.user_id != self.state.get('user_id', None):
            # This is, essentially, a new login.  Start the state clean
            self.state.clear()
            self.state['user_id'] = cert.user_id

        self.state['cert_serial'] = serial

        # Avoid a second "lazy" query later
        # XXX above needs to eagerload the right stuff ugh
        self.user = cert.user

    def login_openid(self, user):
        """Log in via OpenID.

        Need to save the session after this!"""
        # XXX Temporarily drop auth level if user's certs have all expired
        if user.cert_auth == 'required':
            raise OpenIDAuthDisabledError

        if user != self.user:
            if 'cert_serial' in self.state:
                raise CertAuthConflictError

            self.state.clear()
            del self.user

            self.state['user_id'] = user.id

        self.state['openid_timestamp'] = calendar.timegm(datetime.now().timetuple())

    @reify
    def user(self):
        """Returns the currently logged-in user, or a falsey proxy object if
        there is none.
        """
        if 'user_id' in self.state:
            user = meta.Session.query(model.User) \
                .options(joinedload(model.User.role)) \
                .get(self.state['user_id'])
        else:
            user = None

        if not user:
            user = model.AnonymousUser()  # XXX probably move into this file
        return user

    @property
    def can_purge(self):
        return self.user and 'openid_timestamp' in self.state

    @property
    def pending_user(self):
        return False
        # XXX this is mainly used in login.mako, for when the user has logged
        # in with one mechanism but only the other one is allowed

    @property
    def certificate_serial(self):
        """Returns the serial for the active client certificate, or None if
        there isn't one.
        """
        return self.state.get('cert_serial', None)


class Auth():
    """
    Class for managing the authentication status of a user.

    Variables:

    user: model.User() or None
        Instance of a successfully authenticated user, if the Auth
        instance has sufficient authentication mechanisms satisfied
        to meet the requirements of the user's ``User.auth_method``,
        else None.

    satisfied_mechanisms: list [ str:mechanism_name ]
        List of mechansims that have successfully authenticated a user
        with the same id as the ``user`` or ``pending_user``, as
        appropriate.
        If more than one mechanism has been satisfied but for different
        accounts, then the pending user is chosen from the first
        satisfied mechanism as ordered by ``auth_mechanisms``, and this
        list will contain only mechanisms that have been satisfied with
        the ``pending_user``s id.
        If a user is successfully logged in, ``satisfied_mechanisms`` 
        is pruned to only those mechanisms that were used in the
        authentication process.
        Only mechanisms appearing here will be placed in the session
        by save() for re-populating ``mechanisms`` in the following
        request.
        
    required_mechanisms:
    list [ ( str:display_name, str:'required' or str:'sufficient', bool:satisfied ) ]
        List of mechanisms required by the pending user's chosen auth method.
        Essentially just a convenience attribute for showing what mechanisms
        are outstanding to users with pending sessions on the login page.
        Will always be empty if ``pending_user`` is None.

    cert_serial: string (40-digit lower-case hex) or None
        Initialised as the client certificate serial seen in the
        previous request of the session, if any.  Is used by
        _load_certificate() to see if the presented certificate has
        changed and if so is updated to the serial of the certificate
        given in the current session.
        It's main purpose is to act as a staleness indicator for
        _load_certificate(), so the method doesn't have to touch the
        database on every request, but only when a certificate is first
        presented or is changed.
        Necessarily, it persists between requests.

    """

    def can(self, priv, log):
        """Return (True, '') if the current user has the permission priv and
        a sufficient session confidence level to exercise if.  Else return
        a (False, error_string) tuple.

        If log is True, ask the user object to log the privilege exercise.

        """
        if not self.user:
            return False, 'no_user'
        if not self.user.can(priv, log=log):
            return False, 'no_privilege'
        req_confidence = 0
        for lvl in req_confidence_levels:
            for key in req_confidence_levels[lvl]:
                if priv.startswith(key + '.'):
                    req_confidence = lvl
                    break
        if self.confidence_level >= req_confidence:
            return True, ''
        if req_confidence > 1 or (
                req_confidence > 0 and
                self.user.cert_auth in ['required', 'sensitive_required']
                ):
            if not 'cert' in self.satisfied:
                return False, 'cert_auth_required'
            elif self.user.cert_auth not in ['required', 'sensitive_required']:
                return False, 'cert_auth_option_too_weak'
        return False, 'openid_reauth_required'


def stash_request(session, url, post_data=None):
    """Stash the given url and, optionlly, post_data MultiDict, in the given
    session.  Returns a key that may be used to retrieve the stash later.

    The url must be unique among all stashes within a single session.  A new
    stash request with a conflicting url will silently clobber the existing
    stash with that url.

    """
    stashes = session.get('post_stashes', dict())
    # Clean any old pending stashes against this url
    duplicates = [k for k in stashes if stashes[k].get('url', None) == url]
    for k in duplicates:
        del stashes[k]
    key = str(random.getrandbits(64))
    stashes[key] = dict(url=url, post_data=post_data)
    session['post_stashes'] = stashes
    session.save()
    return key

def stash_keys(session):
    """Return all valid stash keys for the given session."""
    return session.get('post_stashes', dict()).keys()

def fetch_stash(session, key):
    """Return the stash associated with the given key if it exists, else None."""
    stashes = session.get('post_stashes', dict())
    return stashes.get(key, None)

def fetch_stash_url(session, key):
    """Return the return URL from the stash associated with the given key if
    it exists, else None."""
    stash = fetch_stash(session, key)
    return stash.get('url', None) if stash else None

def fetch_post(session, request):
    """Return the POST data MultiDict from the stash associated with the given
    key if it exists, else None."""
    if request.method == 'GET' and 'return_key' in request.GET:
        key = request.GET.get('return_key', None)
        stash_item = fetch_stash(session, key)
        if stash_item:
            return stash_item.get('post_data', None)
        else:
            session.flash(u'Unrecognised return key.  Timeout?', level='warning')
    return request.POST

def get_ca(settings):
    """Fetches the Certifiacte Authority certificate and key.

    Returns a (ca_cert, ca_key) tuple, where ca_cert is a pyOpenSSL
    X509 object and ca_key is a pyOpenSSL PKey object.

    """
    cert_dir = settings['client_cert_dir']
    ca_cert_file = os.path.join(cert_dir, 'ca.pem')
    ca_key_file = os.path.join(cert_dir, 'ca.key')
    with open(ca_cert_file, 'rU') as f:
        ca_cert = ssl.load_certificate(ssl.FILETYPE_PEM, f.read())
    with open(ca_key_file, 'rU') as f:
        ca_key = ssl.load_privatekey(ssl.FILETYPE_PEM, f.read())
    return ca_cert, ca_key

def update_crl(settings):
    """Generates a new Certificate Revocation List and writes it to file."""
    crl = ssl.CRL()
    for cert in meta.Session.query(Certificate).filter_by(revoked=True).all():
        r = ssl.Revoked()
        r.set_serial(cert.serial)
        r.set_rev_date(cert.revoked_time.strftime('%Y%m%d%H%M%SZ'))
        crl.add_revoked(r)
    ca_cert, ca_key = get_ca()
    crl_file = os.path.join(settings['client_cert_dir'], 'crl.pem')
    with open(crl_file, 'w') as f:
        f.write(crl.export(ca_cert, ca_key, ssl.FILETYPE_PEM))
