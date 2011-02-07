from datetime import datetime, timedelta
from pylons import config, request
from pylons.controllers.util import abort
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
import time

from floof import model
from floof.lib.helpers import flash
from floof.model import meta

# List methods in decreasing order of authoratativeness
auth_mechanisms = ['cert', 'openid']
auth_mechanism_names = dict(
        cert='SSL Certificate',
        openid='OpenID',
        )
nonpersistent_auth_mechanisms = ['cert']
persistent_auth_mechanisms = [m for m in auth_mechanisms if m not in nonpersistent_auth_mechanisms]

# Similar to PAM.  Unable to model all grouping options if the number
# of available mechanisms >= 4
auth_methods = dict(
        cert_only=[('required', 'cert')],
        openid_only=[('required', 'openid')],
        cert_or_openid=[('sufficient', 'cert'), ('sufficient', 'openid')],
        cert_and_openid=[('required', 'cert'), ('required', 'openid')],
        )

class Auth():
    """
    Class for managing the authentication status of a user.

    Variables:

    user: model.User() or None
        Instance of a successfully authenticated user, if the Auth
        instance has sufficient authentication mechanisms satisfied
        to meet the requirements of the user's ``User.auth_method``,
        else None.

    pending_user: model.User() or None
        Instance of a user that has satisfied at least one authentication
        mechanism (and hence can be identified) but has not satisfied all
        the mechanisms required by their ``User.auth_method``.
        ``pending_user`` and ``user`` are mutually exclusive -- if one is
        a User() instance then the other is None -- although both may be
        None if no authentication mechanisms have been satisfied at all.

    mechanisms: dict { str:mechanism_name : int:authenticate_user_id or None }
        Dictionary mapping all known authentication mechanisms to their
        state.  If they are satisfied, the mapped-to value will be an
        integer representing the user id of the authenticated user, else
        it will be None.
        Its state persists between requests by setting values in the
        session on save() and loading them on class instantiation.

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
        # Load stateful mechanisms states
        self.mechanisms = dict()
        for mech in auth_mechanisms:
            self.mechanisms[mech] = session.get('auth_{0}_user_id'.format(mech), None)
        self.cert_serial = session.get('auth_cert_serial', None)

        # If testing, override the serial
        cert_serial_override = None
        if 'tests.auth_cert_serial' in environ:
            cert_serial_override = environ['tests.auth_cert_serial']

        # Determine stateless mechanisms states
        self._load_certificate(override=cert_serial_override)

        # If testing, override mechanism states as requested
        for mech in self.mechanisms:
            if 'tests.auth_{0}_user_id'.format(mech) in environ:
                self.mechanisms[mech] = environ['tests.auth_{0}_user_id'.format(mech)]

        # Process mechanisms to determine user and other Auth attributes
        self.authenticate()

        if session.last_accessed:
            last_accessed = datetime.fromtimestamp(session.last_accessed)
        else:
            last_accessed = datetime.now()
        inactivity_expiry = int(config.get('inactivity_expiry', 60 * 60))
        max_age = last_accessed + timedelta(seconds=inactivity_expiry)
        if (self.user or self.pending_user) and \
                datetime.now() > max_age and \
                self.can_purge:
            self.purge(session)
            self.authenticate()
            flash(u'Your session has expired and you have been logged out.',
                    icon='user-silhouette')

        # If testing, set the blunt user override
        if 'tests.user_id' in environ:
            self.user = meta.Session.query(model.User) \
                    .options(joinedload('role')) \
                    .filter_by(id=environ['tests.user_id']) \
                    .one()

        # Save any changes to stateful mechanism states or stateless
        # mechanism staleness indicators made during initialization and
        # self.authenticate().
        self.save(session)

    def save(self, session):
        """Save the status of the auth mechanisms to the given session."""
        for mech in auth_mechanisms:
            if mech in self.satisfied_mechanisms:
                session['auth_{0}_user_id'.format(mech)] = self.mechanisms[mech]
            elif 'auth_{0}_user_id'.format(mech) in session:
                del session['auth_{0}_user_id'.format(mech)]
        session['auth_cert_serial'] = self.cert_serial
        session.save()

    def auth_success(self, session, mech, uid):
        """
        Declare the success of the mechanism mech at authenticating UID uid.

        Indicates to Auth that the given mechanism ``mech`` is satisfied
        that the user of the current session owns the account with id
        ``uid`` and immediately saves this to the ``session`` object.

        Returns True if the Auth object now has sufficient authentication
        data to constitute a login, else False.

        """
        self.mechanisms[mech] = uid
        is_sufficient_for_login = self.authenticate()
        self.save(session)
        return is_sufficient_for_login

    def authenticate(self):
        # Derive from the auth_mechanisms list to provide for deterministic
        # precedence between potentially disaperate mechanisms.
        self.pending_id = None
        for mech in auth_mechanisms:
            if self.mechanisms.get(mech, None):
                self.pending_id = self.mechanisms[mech]
                break
        self.user = None
        self.pending_user = None
        self.required_mechanisms = []
        self.satisfied_mechanisms = []
        if self.pending_id:
            self.satisfied_mechanisms = [m for m in self.mechanisms if self.mechanisms[m] == self.pending_id]
            user = meta.Session.query(model.User) \
                    .options(joinedload('role'), joinedload('certificates')) \
                    .filter_by(id=self.pending_id) \
                    .one()
            if user.auth_method in ['cert_only', 'cert_and_openid'] and \
                    not user.valid_certificates:
                user.auth_method = 'cert_or_openid'
            successful_mechs = []
            for req in auth_methods[user.auth_method]:
                if req[0] == 'sufficient' and req[1] in self.satisfied_mechanisms:
                    successful_mechs.append(req[1])
                    break
                elif req[0] == 'required' and req[1] in self.satisfied_mechanisms:
                    successful_mechs.append(req[1])
                elif req[0] == 'required' and req[1] not in self.satisfied_mechanisms:
                    successful_mechs = []
                    break
            if successful_mechs:
                self.user = user
                # Drop any cached authentication successes that are not
                # necessary for the current log in.
                self.satisfied_mechanisms = successful_mechs
            else:
                self.pending_user = user
                self.required_mechanisms = [(auth_mechanism_names[m[1]], m[0], m[1] in self.satisfied_mechanisms) for m in auth_methods[self.pending_user.auth_method]]
        self.can_purge = reduce(lambda p, m: p or m in persistent_auth_mechanisms, self.satisfied_mechanisms, False)
        return bool(self.user)

    def get_user(self):
        """Convenience method: will return the authed user or AnonymousUser()."""
        return self.user if self.user else model.AnonymousUser()

    def purge(self, session):
        """Removes all the cached authentications it can from the session."""
        for mech in persistent_auth_mechanisms:
            self.mechanisms[mech] = None
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
            if self.cert_serial != serial or not self.mechanisms['cert']:
                # New certificate presented
                self.cert_serial = None
                self.mechanisms['cert'] = None
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
                    self.mechanisms['cert'] = cert.user.id
        else:
            # Protect against stale data
            self.cert_serial = None
            self.mechanisms['cert'] = None
