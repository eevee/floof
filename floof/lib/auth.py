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

persistant_variables = [
        'openid_uid',
        'openid_url',
        'openid_age',
        'cert_uid',
        'cert_serial',
        ]

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

        # If testing, override the serial as requested
        cert_serial_override = None
        if 'tests.auth_cert_serial' in environ:
            cert_serial_override = environ['tests.auth_cert_serial']

        # Grab the client certificate, if any
        self._load_certificate(override=cert_serial_override)

        # If testing, override mechanism states as requested
        for mech in ['cert', 'openid']:
            if 'tests.auth_{0}_uid'.format(mech) in environ:
                setattr(self, '{0}_uid'.format(mech), environ['tests.auth_{0}_uid'.format(mech)])

        # Process mechanisms to determine user and other Auth attributes
        self.authenticate()

        # Perform session expiry
        if session.last_accessed:
            last_accessed = datetime.fromtimestamp(session.last_accessed)
        else:
            last_accessed = datetime.now()
        if self.openid_age is not None:
            self.openid_age += datetime.now() - last_accessed
###        inactivity_expiry = int(config.get('inactivity_expiry', 60 * 60))
###        max_age = last_accessed + timedelta(seconds=inactivity_expiry)
###        if (self.user or self.pending_user) and \
###                datetime.now() > max_age and \
###                self.can_purge:
###            self.purge(session)
###            self.authenticate()
###            flash(u'Your session has expired and you have been logged out.',
###                    icon='user-silhouette')

        # If testing, set the blunt user override
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
                # Drop auth level if user's certs have all expired
                user.cert_auth = 'allowed'
            if (user.cert_auth != 'disabled' and self.cert_uid) or \
                    (user.cert_auth != 'required' and self.openid_uid):
                # Successful login
                self.user = user
            else:
                self.pending_user = user
        print self.satisfied
        self.can_purge = len(self.satisfied) == 1 and self.satisfied[0] == 'openid'
        return bool(self.user)

    def get_confidence_level(self):
        if not self.user:
            return -1
        if not self.openid_age:
            return 0
        if self.user.cert_auth in ['required', 'sensitive_required']:
            if self.cert_uid and self.openid_age <= timedelta(minutes=30):
                return 2
        elif self.openid_age <= timedelta(minutes=10):
            return 1
        return 0

    confidence_level = property(get_confidence_level)

    def get_user(self):
        """Convenience method: will return the authed user or AnonymousUser()."""
        return self.user if self.user else model.AnonymousUser()

    def openid_success(self, session, uid, url):
        self.openid_uid = uid
        self.openid_url = url
        self.openid_age = timedelta(0)
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
