# encoding: utf-8
"""
This module deals primarily with authentication, as well as providing some
authorization helpers that inspect authentication state.

"""
import calendar
import logging
import OpenSSL.crypto as ssl
import os.path

from datetime import datetime, timedelta
from functools import partial

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated, Everyone
from pyramid.security import effective_principals, has_permission
from pyramid.security import principals_allowed_by_permission
from pyramid.settings import asbool
from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm.exc import NoResultFound
from zope.interface import implements

from floof import model
from floof.resource import contextualize

log = logging.getLogger(__name__)

DEFAULT_CONFIDENCE_EXPIRY = 60 * 10  # seconds

UPGRADABLE_PRINCIPALS = ('auth:', 'trusted:')

TRUST_MAP = dict([
    ('trusted_for:auth', [
        ('role:user', 'auth:insecure', 'trusted:openid_recent'),
        ('role:user', 'auth:insecure', 'trusted:cert'),
        ('role:user', 'auth:secure', 'trusted:cert'),
    ]),
    ('trusted_for:admin', [
        ('role:admin', 'auth:secure', 'trusted:cert'),
    ]),
])
"""A dictionary mapping :term:`derived principal` identifiers to a list of
n-tuples of pre-requisite :term:`principal` identifiers.  If
:class:`FloofAuthnPolicy` is the authentication policy in effect, then each
:term:`derived principal` is granted to any user that holds all of the
pre-requisite :term:`principal` identifiers in any tuple within that derived
principal's mapped list.

The point is to allow for principals that arise from holding a combination of:

- ``role:*`` principals, which are granted manually by administrators;

- ``auth:*`` principals, which reflect to the relative strength of the user's
  chosen auth method; and

- ``trusted:*`` principals, which reflect the valid authentication mechanisms
  in the context of the current request.

"""


class FloofAuthnPolicy(object):
    """Pyramid style authentication policy bolted atop a beaker session.

    Most of the actual work here is done by :class:`Authenticizer`, an instance
    of which should be attached to the `request` as ``request.auth``.

    The Pyramid auth interface is extremely clunky, and this class only exists
    so standard Pyramid authorization stuff still works.

    """
    implements(IAuthenticationPolicy)

    def authenticated_userid(self, request):
        raise NotImplementedError()

    def unauthenticated_userid(self, request):
        raise NotImplementedError()

    def effective_principals(self, request):
        """Returns the list of 'effective' :term:`principal` identifiers for
        the request."""

        user = request.auth.user
        principals = set([Everyone])

        if not user:
            return principals

        principals.add(Authenticated)
        principals.update(['user:' + str(user.id)])
        principals.update('role:' + role.name for role in user.roles)
        principals.update('trusted:' + flag for flag in request.auth.trust)

        if user.cert_auth in ('required', 'sensitive_required'):
            principals.add('auth:secure')
        else:
            principals.add('auth:insecure')

        # Add derived principals
        for derivative, prereqs_list in TRUST_MAP.iteritems():
            for prereqs in prereqs_list:
                f = lambda x: x in principals
                if all(map(f, prereqs)):
                    principals.add(derivative)
                    break

        return principals

    def remember(self, request, user, openid_url=None, **kw):
        """Remembers a set of (stateful) credentials authenticating the `user`.

        Deviates from the Pyramid authentication policy model in that
        `principal` is the user (as an SQLAlchemy model object) not a
        principal.

        At present, only accepts calls that include both a `user` and an
        `openid_url` parameter.

        """
        if openid_url:
            request.auth.login_openid(user, openid_url)
        else:
            raise ValueError("A credential, such as openid_url, must be "
                             "passed to this function.")

        # Renew session identifier on persistant (non-cert) authn status change
        # (a best practice).  Such renewal is not part of the Pyramid session
        # interface, so conditionally check for the regenerate_id method that
        # is present on Beaker sessions
        if hasattr(request.session, 'regenerate_id'):
            request.session.regenerate_id()

        request.session.save()
        return []

    def forget(self, request):
        """Purges all purgable authentication data from the
        :class:`Authenticizer` at ``request.auth``."""

        request.auth.clear()
        request.session.save()
        return []


class CertNotFoundError(Exception): pass
class CertAuthDisabledError(Exception): pass
class CertExpiredError(Exception): pass
class CertRevokedError(Exception): pass
class OpenIDAuthDisabledError(Exception): pass
class OpenIDNotFoundError(Exception): pass
class AuthConflictError(Exception): pass


class Authenticizer(object):
    """Manages the authentication and authorization state of the current user.

    This class is intended to be instantiated from a Request object.  The
    :class:`FloofAuthnPolicy` class expects to find an instance of this class
    on the request, and delegates Pyramid security functionality here.

    To perform authentication and identity resolution, the constructor calls a
    series of methods, one for each supported authentication mechanism.  These
    methods are prefixed with ``check_`` and have the following obligations:

    1. If they cannot resolve a valid authentication, they must clear any
       authentication information related to the authentication mechanism that
       they handle from :attr:`state`;

    2. If they resolve a valid authentication, and this differs from the
       prevailing value of :attr:`user`, they again must clear any
       authentication information that they may have set (in a previous
       request) from :attr:`state`;

    3. If they resolve a valid authentication, and this agrees with the
       prevailing value of :attr:`user` (or :attr:`user` is None), they must
       add any related authentication information to :attr:`state` and append
       appropriate flags to :attr:`trust`.  If :attr:`user` is None, they must
       set it to the resolved user; and

    4. If the authentication fails or is invalid or inconsistent, they should
       raise a relevant error and be sure to catch it in the constructor.

    Note: everything within :attr:`state` is meant to be consistent at all
    times; i.e., there should never be a cert serial, openid, or user id
    that don't all match.

    """

    _cred_tokens = ['cert_serial', 'openid_url', 'openid_timestamp']
    _trust_flags = ['cert', 'openid', 'openid_recent']

    def __init__(self, request):
        config = request.registry.settings

        # Attributes
        self.state = request.session.setdefault('auth', {})
        """A reference to `request.session['auth']`, a dictionary that contains
        all of the state information needed by :class:`Authenticizer` between
        requests."""

        self.user = model.AnonymousUser()
        """Either the user authenticated by the state of the various
        authentication mechanisms of :class:`Authenticizer` (listed in
        :attr:`trust`) or an instance of :class:`floof.model.AnonymousUser`."""

        self.trust = []  # XXX Work out a better name
        """A list of authentication mechanisms satisfied that the current
        request authenticates :attr:`user`."""

        # convenience/readability helper
        error = partial(request.session.flash, level='error',
                        icon='key--exclamation')

        # TODO: move the below into check_certificate or its own method
        verified_serial = None
        if 'paste.testing' in request.environ:
            self._setup_testing_early(request)
            verified_serial = request.environ.get('tests.auth.cert_serial')

        # Check for client certificate serial; ATM, the cert serial is passed
        # by the frontend server in an HTTP header.
        if asbool(config.get('auth.certs.enabled')) and not verified_serial:
            # need to check verification status if we pass requests failing
            # cert auth back to floof (e.g. for user help display)
            # XXX the below 'verify' codes are nginx-isms
            verify = request.headers.get('X-Floof-SSL-Client-Verify')
            serial = request.headers.get('X-Floof-SSL-Client-Serial', '')
            serial = serial.lower()

            if verify == 'SUCCESS':
                verified_serial = serial
                log.debug("Successful verification of cert with claimed "
                          "serial '{0}'".format(serial))

            elif verify == 'FAILED':
                error("You are presenting an invalid certificate.")
                log.warning("Unsuccessful verification of cert with claimed "
                            "serial '{0}'".format(serial))

        try:
            self.check_certificate(verified_serial)
        except CertNotFoundError:
            log.error("A validated client cert was not found in the DB, yet "
                      "client certs should persist in the DB indefinately.")
            error("I don't recognize your client certificate.")
        except CertAuthDisabledError:
            error("Client certificates are disabled for your account.")
        except CertExpiredError:
            error("That client certificate has expired.")
        except CertRevokedError:
            error("That client certificate has been revoked.")

        try:
            self.check_openid(config)
        except OpenIDNotFoundError:
            error("I don't recognize your OpenID identity.")
        except OpenIDAuthDisabledError:
            error("Your OpenID is no longer accepted as your account has disabled OpenID authentication.")
        except AuthConflictError:
            error("Your OpenID conflicted with your certificate and has been cleared.")

        if 'paste.testing' in request.environ:
            self._setup_testing_late(request)

        if len(self.trust) == 0:
            # Either there's no user, or none of their current auths are valid.
            # Wipe the slate clean
            self.clear()

        print self, request.url
        request.session.changed()

        # for convenience
        def user_can(permission, context=None):
            """Returns True if the current user can (potentially after re-auth
            and/or a settings change) have the given permission in the given
            context, else False.  context defaults to request.context."""
            if context is None:
                context = request.context
            return could_have_permission(permission, context, request)

        self.user.can = user_can

    def _setup_testing_early(self, request):
        """Setup any requested test credential tokens."""

        self.clear()
        env = request.environ

        if 'tests.user_id' in env:
            self.user = model.session.query(model.User).get(
                    env['tests.user_id'])

        else:
            for token in self._cred_tokens:
                idx = 'tests.auth.' + token
                if idx in env:
                    self.state[token] = env[idx]

    def _setup_testing_late(self, request):
        """Override trust flags as requested or required."""

        env = request.environ
        if ('tests.auth_trust' in env or 'tests.user_id' in env):
            self.trust = env.get('tests.auth_trust', self._trust_flags)

    def check_certificate(self, serial):
        """Check a client certificate serial and add authentication if valid."""

        self.state.pop('cert_serial', None)

        if not serial:
            # No cert. Our obligation to wipe cert state is fulfilled above.
            return

        # Figure out what certificate and user this serial belongs to
        # TODO: Optimize eagerloading
        serial = serial.lower()
        q = model.session.query(model.Certificate) \
            .options(joinedload_all('user.roles')) \
            .filter_by(serial=serial)

        try:
            cert = q.one()
        except NoResultFound:
            raise CertNotFoundError

        if cert.user.cert_auth == u'disabled':
            raise CertAuthDisabledError
        if cert.expired:
            raise CertExpiredError
        if cert.revoked:
            raise CertRevokedError
        if self.user and self.user.id != cert.user_id:
            raise AuthConflictError

        # At this point, we're confident that the supplied cert is valid

        self.state['cert_serial'] = serial
        self.trust.append('cert')

        if not self.user:
            self.user = cert.user

    def check_openid(self, config):
        """Check OpenID state and add authentication if valid, else clear."""

        url = self.state.pop('openid_url', None)
        timestamp = self.state.pop('openid_timestamp', None)

        if not url or timestamp is None:
            # No (or corrupted) OpenID login. By popping, our obligation to
            # clear relevent state is already fulfilled, so just return
            return

        # TODO: Optimize eagerloading
        q = model.session.query(model.IdentityURL) \
            .options(joinedload_all('user.roles')) \
            .filter_by(url=url)

        try:
            openid = q.one()
        except NoResultFound:
            raise OpenIDNotFoundError

        if openid.user.cert_auth == 'required':
            raise OpenIDAuthDisabledError
        if self.user and self.user.id != openid.user_id:
            raise AuthConflictError

        # XXX Check timestamp sanity?
        # At this point, we're confident that the stored OpenID login is valid

        self.state['openid_url'] = url
        self.state['openid_timestamp'] = timestamp
        self.trust.append('openid')

        # Evaluate OpenID freshness
        confidence_expiry_secs = int(config.get(
            'auth.openid.expiry_seconds',
            DEFAULT_CONFIDENCE_EXPIRY))

        age = datetime.now() - datetime.fromtimestamp(timestamp)
        if age <= timedelta(seconds=confidence_expiry_secs):
            self.trust.append('openid_recent')

        if not self.user:
            self.user = openid.user

    def login_openid(self, user, url):
        """Log in via OpenID, adding appropriate authentication state.

        Remember that any authentication change will only take effect on the
        next request.  The typical scenario is that the user is redirected at
        the end of a request that calls this method.

        Also remember to save the session after this!
        """
        # XXX Temporarily drop auth level if user's certs have all expired

        if user.cert_auth == 'required':
            raise OpenIDAuthDisabledError
        if not url in (u.url for u in user.identity_urls):
            raise OpenIDNotFoundError

        self.state['openid_url'] = url
        self.state['openid_timestamp'] = calendar.timegm(datetime.now().timetuple())

    def clear(self):
        """Log the user out completely."""
        # TODO what shall this do with certificates
        self.state.clear()
        self.user = model.AnonymousUser()
        self.trust = []

    @property
    def can_purge(self):
        return 'openid' in self.trust

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

    def __repr__(self):
        openid_age = None
        if 'openid_timestamp' in self.state:
            openid_age = datetime.now() - datetime.fromtimestamp(
                    self.state['openid_timestamp'])

        return ("<Authenticizer ( User: {0}, Cert: {1}, OpenID URL: {2}, "
                "OpenID Age: {3}, Trust Flags: {4} )>".format(
                    self.user.name if self.user else None,
                    self.state.get('cert_serial', None),
                    self.state.get('openid_url', None),
                    openid_age,
                    repr(self.trust),
                    ))


def get_ca(settings):
    """Fetches the Certifiacte Authority certificate and key.

    Returns a (ca_cert, ca_key) tuple, where ca_cert is a pyOpenSSL
    X509 object and ca_key is a pyOpenSSL PKey object.

    `settings` is a Pyramid `deployment settings` object, typically
    ``request.registry.settings``

    """
    cert_dir = settings['auth.certs.directory']
    ca_cert_file = os.path.join(cert_dir, 'ca.pem')
    ca_key_file = os.path.join(cert_dir, 'ca.key')

    with open(ca_cert_file, 'rU') as f:
        ca_cert = ssl.load_certificate(ssl.FILETYPE_PEM, f.read())

    with open(ca_key_file, 'rU') as f:
        ca_key = ssl.load_privatekey(ssl.FILETYPE_PEM, f.read())

    return ca_cert, ca_key

# The following functions mostly assist with Authentication Upgrade.
# Authentication Upgrade refers to increasing the expected strength of a
# users's authentication to the system, generally with the goal of gaining
# additional principals and thus additional authorization.
# It may occur through adding an authentication token (providing a cert or
# logging in with OpenID) by renewing an expireable token (e.g. renewing an
# OpenID login) or by changing to an authentication method setting that is
# considered more secure.
# The key point is that the user may perform the upgrade autonomously -- no new
# permissions need to be administratively granted.

def permissions_in_context(context, request):
    """Returns a list of (permission, allowed) tuples for each permission
    defined in the ACL (``__acl__``) of the `context`.  allowed is a boolean
    that is True if ``request.user`` holds that permission in that context."""

    acl = getattr(context, '__acl__', None)

    if not acl:
        return []

    permissions = set()
    for action, principal, perms in acl:
        if not hasattr(perms, '__iter__'):
            perms = [perms]
        permissions.update(set(perms))

    results = []
    for perm in sorted(permissions):
        results.append((perm, request.user.can(perm, context)))

    return results

def outstanding_principals(permission, context, request):
    """Returns a list of sets of principals, where the attainment of all of the
    principals in any one of the sets would be sufficient to grant the current
    user (``request.user``) the `permission` in the given `context`."""

    # TODO be able to determine a context based on a route name

    if has_permission(permission, context, request):
        return []

    principals = principals_allowed_by_permission(context, permission)
    if not principals:
        # the permission must not exist at all within this context
        return ['__unattainable__']

    effective = set(effective_principals(request))
    outstanding = []

    for p in principals:
        if p in TRUST_MAP:
            for alternative_principals in TRUST_MAP[p]:
                diff = set(alternative_principals) - effective
                if len(diff) > 0 and 'auth:insecure' not in diff:
                    outstanding.append(diff)
        else:
            outstanding.append(set([p]))

    return outstanding

def could_have_permission(permission, context, request):
    """Returns True if the current user (``request.user``) either holds the
    `permission` in the given `context` or could hold it after
    :term:`authentication upgrade`."""

    if context is None:
        return False

    if not hasattr(context, '__acl__'):
        # XXX is this bit of convenience appropriate?
        context = contextualize(context)

    outstanding = outstanding_principals(permission, context, request)

    if not outstanding:
        return True

    # The user can gain the permission only if there is an alternative set in
    # their outstanding_principals list of sets containing only upgradable
    # principal types.
    for altset in outstanding:
        f = lambda x: x.startswith(UPGRADABLE_PRINCIPALS)
        if all(map(f, altset)):
            return True

    return False

def attempt_privilege_escalation(permission, context, request):
    """Try to automatically guide the user through elevating their privileges.

    If it is possible to automatically guide the user to gain the privileges
    needed to gain the given permission in the given context, do so.  This may
    entail setting a stash for the current request then redirecting.

    """
    if not could_have_permission(permission, context, request):
        return

    for altset in outstanding_principals(permission, context, request):
        if len(altset) != 1:
            continue

        principal = altset.pop()

        if principal in ('trusted:openid', 'trusted:openid_recent'):
            # Can elevate by performing an OpenID authentication; so set a
            # return_key and redirect to the login screen
            from floof.lib.stash import stash_post
            from pyramid.httpexceptions import HTTPSeeOther

            key = stash_post(request)
            request.session.flash("You need to re-authenticate with an OpenID "
                                  "identity to complete this action",
                                  level='notice')

            raise HTTPSeeOther(location=request.route_url(
                    'account.login', _query=[('return_key', key)]))

def current_view_permission(request):
    """Returns the permission on the current (non-error) view or None.

    Only works with URL Dispatch at present.

    """
    # HACK: uses non-API classes
    # And lo, epii reached forth unto the bowels of Pyramid to retrieve that
    # permission attached to the view reached by the current request, and there
    # was much wailing and gnashing of teeth.
    # XXX may not yet work with pages that replace context with a ORM object

    from pyramid.config.views import MultiView
    from pyramid.interfaces import IMultiView
    from pyramid.interfaces import ISecuredView
    from pyramid.interfaces import IView
    from pyramid.interfaces import IViewClassifier
    from zope.interface import providedBy

    request_iface = request.request_iface
    r_context = providedBy(request.context)

    for view_type in (IView, ISecuredView, IMultiView):
        view = request.registry.adapters.lookup(
            (IViewClassifier, request_iface, r_context),
            view_type)
        if view is not None:
            break

    if isinstance(view, MultiView):
        view = view.match(request.context, request)

    if view is None or not hasattr(view, '__permission__'):
        return None

    return view.__permission__


# The following are help messages for user-upgradable privileges
# XXX this is ugly, ugh

MSG_PRESENT_CERT = 'Present your client certificate for authentication'
MSG_GEN_CERT = 'Generate and configure a client certificate'
MSG_AUTH_SEC = (
        "Configure your certificate authentication option to either "
        "'Require using client certificates for login' or 'Allow using "
        "client certificates for login; Required for Sensitive Operations'")

def help_auth_secure(request):
    msg = ''
    if len(request.user.certificates) < 1:
        msg += MSG_GEN_CERT
    msg += MSG_AUTH_SEC
    return msg

def help_trusted_cert(request):
    msg = ''
    if len(request.user.certificates) < 1:
        msg += MSG_GEN_CERT
    msg += MSG_PRESENT_CERT
    return msg

def help_trusted_openid(request):
    return "Authenticate with OpenID"

def help_trusted_openid_recent(request):
    if 'trust:openid' in effective_principals(request):
        return "Re-authenticate with your OpenID"
    return help_trusted_openid(request)

auth_actions = dict([
    ('auth:secure', help_auth_secure),
    ('trusted:cert', help_trusted_cert),
    ('trusted:openid', help_trusted_openid),
    ('trusted:openid_recent', help_trusted_openid_recent),
])
