from datetime import datetime, timedelta
from pylons import config, request
from pylons.controllers.util import abort
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from floof import model
from floof.lib.helpers import flash
from floof.model import meta, Certificate

import OpenSSL.crypto as ssl
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

    def __init__(self, session, environ):
        # Load OpenID state and certificate cache values
        for var in persistant_variables:
            setattr(self, var, session.get(var, None))

        # Grab the client certificate, if any
        # If testing, override the serial as requested
        self._load_certificate(override=environ.get('tests.auth_cert_serial', None))

        # If testing, override mechanism states as requested
        for var in persistant_variables:
            if 'tests.auth_{0}'.format(var) in environ:
                setattr(self, var, environ['tests.auth_{0}'.format(var)])

        # Process mechanisms to determine user and other Auth attributes
        self.authenticate()

        # If testing, set the blunt user override as requested
        if 'tests.user_id' in environ:
            self.user = meta.Session.query(model.User) \
                    .options(joinedload('role')) \
                    .filter_by(id=environ['tests.user_id']) \
                    .one()

        # Save any changes made during initialization and self.authenticate()
        self.save(session)

    def save(self, session):
        """Save the authentication status to the given session."""
        for var in persistant_variables:
            session[var] = getattr(self, var)
        session.save()

    def authenticate(self):
        self.user = None
        self.pending_user = None
        if self.cert_uid and self.cert_uid != self.openid_uid:
            self.openid_uid = None
        self.satisfied = []
        for auth in ['cert', 'openid']:
            if getattr(self, '{0}_uid'.format(auth)):
                self.satisfied.append(auth)
        if self.satisfied:
            uid = self.cert_uid or self.openid_uid
            user = meta.Session.query(model.User) \
                    .options(joinedload('role'), joinedload('certificates')) \
                    .filter_by(id=uid) \
                    .one()
            if user.cert_auth in ['required', 'sensitive_required'] and \
                    not user.valid_certificates:
                # Temporarily drop auth level if user's certs have all expired
                user.cert_auth = 'allowed'
            if (user.cert_auth != 'disabled' and self.cert_uid) or \
                    (user.cert_auth != 'required' and self.openid_uid):
                # Successful login
                self.user = user
            else:
                self.pending_user = user
        return bool(self.user)

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

    def get_can_purge(self):
        """Convenience method: Ccheck if the auth session may be sensibly
        logged out.
        """
        return len(self.satisfied) == 1 and self.satisfied[0] == 'openid'

    can_purge = property(get_can_purge)

    def get_confidence_level(self):
        """Return the current confidence level of the session.

        Based on:
          - Whether the is a user logged in
            (-1 if not).
          - How recently an OpenID authentication was made
            (1 if recently enough, else 0).
          - Whether a certificate required for sensitive actions and one
            is being used to authenticate this session
            (2 if so and the OpenID check passed).

        """
        if not self.user:
            return -1
        if not self.openid_uid or not self.openid_time:
            return 0
        if self.user.cert_auth in ['required', 'sensitive_required']:
            if self.cert_uid and self.openid_age <= timedelta(seconds=CERT_CONFIDENCE_EXPIRY_SECONDS):
                return 2
        elif self.openid_age <= timedelta(seconds=CONFIDENCE_EXPIRY_SECONDS):
            return 1
        return 0

    confidence_level = property(get_confidence_level)

    def get_openid_age(self):
        """Return how long ago the OpenID auth, if any, was refreshed."""
        if self.openid_time:
            return datetime.now() - datetime.fromtimestamp(self.openid_time)
        return None

    openid_age = property(get_openid_age)

    def get_user(self):
        """Convenience method: will return the authed user or AnonymousUser()."""
        return self.user if self.user else model.AnonymousUser()

    def openid_success(self, session, uid, url, auth_time=None):
        """Log the success of an OpenID authentication attempt."""
        if self.user and (
                uid != self.user.id or
                url not in [id.url for id in self.user.identity_urls]
                ):
            return False
        self.openid_uid = uid
        self.openid_url = url
        self.openid_time = time.time()
        is_sufficient_for_login = self.authenticate()
        self.save(session)
        return is_sufficient_for_login

    def purge(self, session):
        """Removes all the cached authentication data it can from the session."""
        for var in persistant_variables:
            setattr(self, var, None)
        self.save(session)

    def _load_certificate(self, override=None):
        """Set up certificate authentication attributes."""
        serial = None
        transport = config.get('client_cert_transport', None)
        if override:
            serial = override
        elif transport == 'http_headers':
            serial = unicode(request.headers.get('X-Floof-SSL-Client-Serial', '').lower())
            if serial and request.headers.get('X-Floof-Secret', '') != config['client_cert_http_secret']:
                abort(500, detail='SSL client certificate Serial header recieved '
                        'but Secret header invalid.  Misconfiguration or attack.')

        if serial and config.get('client_cert_auth', '').lower() == 'true':
            self.cert_serial = None
            self.cert_uid = None
            try:
                cert = meta.Session.query(model.Certificate) \
                        .options(joinedload('user')) \
                        .filter_by(serial=serial) \
                        .one()
            except NoResultFound:
                # Should never happen in production
                # (Certificate records should stand eternal)
                abort(500, detail='Unable to find certificate in store.  '
                        '(Has the certificate record been deleted?)  '
                        'Try not sending your SSL client certificate.')
            if cert and cert.valid:
                self.cert_serial = serial.lower()
                self.cert_uid = cert.user.id
        else:
            # Protect against stale data
            self.cert_serial = None
            self.cert_uid = None

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
            flash(u'Unrecognised return key.  Timeout?', level='warning')
    return request.POST

def get_ca():
    """Fetches the Certifiacte Authority certificate and key.

    Returns a (ca_cert, ca_key) tuple, where ca_cert is a pyOpenSSL
    X509 object and ca_key is a pyOpenSSL PKey object.

    """
    cert_dir = config['client_cert_dir']
    ca_cert_file = os.path.join(cert_dir, 'ca.pem')
    ca_key_file = os.path.join(cert_dir, 'ca.key')
    with open(ca_cert_file, 'rU') as f:
        ca_cert = ssl.load_certificate(ssl.FILETYPE_PEM, f.read())
    with open(ca_key_file, 'rU') as f:
        ca_key = ssl.load_privatekey(ssl.FILETYPE_PEM, f.read())
    return ca_cert, ca_key

def update_crl():
    """Generates a new Certificate Revocation List and writes it to file."""
    crl = ssl.CRL()
    for cert in meta.Session.query(Certificate).filter_by(revoked=True).all():
        r = ssl.Revoked()
        r.set_serial(cert.serial)
        r.set_rev_date(cert.revoked_time.strftime('%Y%m%d%H%M%SZ'))
        crl.add_revoked(r)
    ca_cert, ca_key = get_ca()
    crl_file = os.path.join(config['client_cert_dir'], 'crl.pem')
    with open(crl_file, 'w') as f:
        f.write(crl.export(ca_cert, ca_key, ssl.FILETYPE_PEM))
