"""
This module contains the :class:`PrivCheck` compound principal class, the
floof version of Pyramid's ACLAuthorizationPolicy required to work with it, and
anciallary functions that mostly assist with Authentication Upgrade.

Authentication Upgrade refers to increasing the expected strength of a user's
authentication to the system, generally with the goal of gaining additional
principals and thus additional authorization.

It may occur through adding an authentication token (providing a cert or
logging in with OpenID) by renewing an expireable token (e.g. renewing an
OpenID login) or by changing to an authentication method setting that is
considered more secure.

The key point is that the user may perform the upgrade autonomously -- no new
permissions need to be administratively granted.

"""
import logging

from itertools import product

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.compat import is_nonstr_iter
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.location import lineage
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import ACLAllowed, ACLDenied, Allow, Authenticated
from pyramid.security import effective_principals, has_permission
from pyramid.security import principals_allowed_by_permission

from floof.lib.stash import stash_post


log = logging.getLogger(__name__)

UPGRADABLE_PRINCIPALS = ('auth:', 'cred:')

TRUST_MAP = dict([
    ('trusted_for:auth', [
        ('auth:insecure', 'cred:browserid_recent'),
        ('auth:insecure', 'cred:openid_recent'),
        ('auth:insecure', 'cred:cert'),
        ('auth:secure', 'cred:cert'),
    ]),
    ('trusted_for:admin', [
        ('auth:secure', 'cred:cert'),
    ]),
])
"""A dictionary mapping :term:`derived principal` identifiers to a list of
n-tuples of pre-requisite :term:`principal` identifiers.  These may be selected
as the ``trusted_for`` argument to the :class:`PrivCheck` pseudo-principal.

The point is to allow for principals that arise from holding a combination of:

- ``auth:*`` principals, which reflect to the relative strength of the user's
  chosen auth method; and

- ``cred:*`` principals, which reflect the valid authentication mechanisms
  in the context of the current request.

"""


ROLE_ORDER = (
    'admin',
    'moderator',
    'curator',
    'user',
)
"""A tuple defining the linear hierarchy of roles.  Roles listed earlier hold a
strict superset of the (potential) privileges of those listed later."""


def flatten(iterable):
    """Recursively flatten a nested non-str iterable; returns a list."""
    if not is_nonstr_iter(iterable):
        return iterable
    flattened = []
    for element in iterable:
        flat = flatten(element)
        flat = flat if is_nonstr_iter(flat) else [flat]
        flattened.extend(flat)
    return flattened


class PrivCheck(object):
    """Acts as a complex/compound principal for use in ACLs.

    Provides a way to encapsulate complex rules for requiring particular
    combinations of basic, string-based principals.  The core interface is: the
    complex principal object should be a callable that, called with the
    session's current `principals`, will return True if its conditions are
    satisfied and False otherwise.  For the sake of floof's "authenication
    upgrade" crud, it also provides the methods :meth:`delta` and
    :meth:`upgradeable`.

    While it is hoped that the interface should be extendable to any
    encapsulation of complex principal requirements, this particular class aims
    to help in the common case of requiring the client to:

    -  Act for a user with a particular role or better;
    -  Act for a particular user;
    -  Hold a particular scope authorization if an OAuth client; and
    -  Hold a particular set of authentication credentials while acting for a
       user with particular authentication settings (chosen from a predefined
       set given by :const:`TRUST_MAP`).

    Or just a subset thereof.

    This class will deny OAuth clients by default; to permit their access
    specify a value for the ``scope`` constructor argument.  It is assumed that
    browser-based access is always permitted and that OAuth is the only
    non-browser-based access mechanism.

    NB: Whenever it is necessary to denote the required absence of a string
    principal, a "-" with be prepended to the principal name.  E.g.
    "-cred:oauth" means that, to satisfy the instance, the principals must
    exclude "cred:oauth" (and hence the active session must not be an OAuth
    client).

    """
    def __init__(self, role=None, user_id=None, scope=None, trusted_for=None):
        # Sanity checks
        if role and role not in ROLE_ORDER:
            raise ValueError('No such role: "{0}".'.format(role))
        if trusted_for and 'trusted_for:' + trusted_for not in TRUST_MAP:
            raise ValueError('No such trusted_for: "{0}".'.format(trusted_for))

        self.role = role
        self.user_id = str(user_id) if user_id else None
        self.scope = scope
        self.trusted_for = trusted_for

        # Select the chosen role *and* all roles superior to it
        self.roles = ROLE_ORDER[:ROLE_ORDER.index(role) + 1]

    def __call__(self, principals):
        """Returns True if the ``principals`` satisfy the instance."""
        return not self.delta(principals, cleanup=False)

    def delta(self, principals, cleanup=True):
        """Find the difference between the given ``principals`` and those
        required to satisfy the :class:`PrivCheck` instance.

        The representation of the result depends on the ``cleanup`` argument.

        If True (the default) the output is a set of tuples of simple string
        principals.  Obtaining all principals in any tuple in the set (in
        addition to any current ones) should be sufficient to satify the
        :class:`PrivCheck` instance.  e.g.:

        >>> chk = PrivCheck(role='admin', user_id=1, trusted_for='admin')
        >>> principals = [Authenticated, 'role:user', 'user:1', 'auth:secure', 'cred:openid']
        >>> chk.delta(principals)
        set([('role:admin', 'cred:cert')])

        If False, the output is a list of unfulfilled principal categories,
        with each category being a list of principals, a combination thereof,
        or some other token, the format of which is not guaranteed.
        Additionally, no effort is made to ensure that all principals listed
        are not already held, e.g.:

        >>> chk.delta(principals, cleanup=False)
        [['role:admin'], [('auth:secure', 'cred:cert')]]

        Note that 'auth:secure' is listed even though it is already in
        ``principals`` because it's "hidden" within a tuple.  The tuple itself
        is not redundant as 'cred:cert' is indeed not in ``principals``.

        In either case, a result that evaluates after bool() to False indicates
        that the :class:`PrivCheck` instance is already satisfied by the given
        ``principals``.

        >>> chk.delta([Authenticated, 'role:admin', 'auth:secure', 'cred:openid'])
        set([('user:1', 'cred:cert')])
        >>> chk = PrivCheck(role='admin', scope='art')
        >>> chk.delta([Authenticated, 'role:admin', 'cred:borwserid'])
        set([])
        >>> chk.delta([Authenticated, 'role:admin', 'cred:oauth', 'scope:art'])
        set([])
        >>> chk.delta([Authenticated, 'role:admin', 'scope:art'])
        set([])
        >>> chk.delta([Authenticated, 'role:admin', 'cred:oauth', 'scope:comment', 'scope:fancy_hats'])
        set([('-cred:oauth',), ('scope:art',)])

        """
        factors = []

        if not Authenticated in principals:
            factors.append([Authenticated])
        if not any('role:' + r in principals for r in self.roles):
            factors.append(['role:' + r for r in self.roles])
        if self.user_id and 'user:' + self.user_id not in principals:
            factors.append(['user:' + self.user_id])
        if 'cred:oauth' in principals:
            if not self.scope:
                factors.append(['-cred:oauth'])
            elif 'scope:' + self.scope not in principals:
                factors.append(['-cred:oauth', 'scope:' + self.scope])
        if self.trusted_for:
            alternatives = TRUST_MAP['trusted_for:' + self.trusted_for]
            if not any(all(p in principals for p in option)
                       for option in alternatives):
                factors.append(alternatives)

        if not cleanup:
            return factors

        # Some prinicpals may be 'bundled' as a sub-list or tuple when the
        # cartesian product is taken (think auth: and cred: in trusted_for);
        # don't forget to strip any bundled principals that we actually posess
        flattened = [flatten(p) for p in product(*factors)]
        groups = [tuple(p for p in group if p and p not in principals)
                  for group in flattened]
        return set(g for g in groups if g)

    @reify
    def principals(self):
        r"""Return a list of lists of simple string principals.  Satisfying all
        principals within any inner list will be sufficient to satisfy the
        :class:`PrivCheck` instance.  e.g.:

        >>> PrivCheck(role='moderator', trusted_for='admin').principals
        [['role:admin', '-cred:oauth', 'auth:secure', 'cred:cert'], ['role:moderator', '-cred:oauth', 'auth:secure', 'cred:cert']]
        >>> PrivCheck(role='admin', scope='art').principals
        [['role:admin', '-cred:oauth'], ['role:admin', 'scope:art']]

        NB: This is only meant as a manual debugging aid.  The principal
        'system.Authenticated' is omitted from the output for brevity.

        """
        factors = []
        if self.role:
            factors.append(['role:' + r for r in self.roles])
        if self.user_id:
            factors.append(['user:' + self.user_id])
        if self.scope:
            factors.append(['-cred:oauth', 'scope:' + self.scope])
        else:
            factors.append(['-cred:oauth'])
        if self.trusted_for:
            factors.append(TRUST_MAP['trusted_for:' + self.trusted_for])
        return [flatten(p) for p in product(*factors)]

    def upgradeable(self, principals):
        """Returns True if the user can upgrade their permissions autonomously.

        The only principals over which all users have direct control are the
        'auth:' and 'cred:' principals selected by the ``trusted_for``
        argument to the :class:`PrivCheck` constructor.  In essence then, this
        method checks whether ``trusted_for`` is the only limiting argument.

        """
        return (
            self.trusted_for and
            not self(principals) and
            PrivCheck(self.role, self.user_id, self.scope)(principals)
        )

    def __repr__(self):
        ret = '<PrivCheck'
        for arg in ('role', 'user_id', 'scope', 'trusted_for'):
            argval = getattr(self, arg)
            if argval:
                ret += ' {0}={1}'.format(arg, argval)
        return ret + '>'


class FloofACLAuthorizationPolicy(ACLAuthorizationPolicy):
    """Like Pyramid's default
    :class:`pyramid.authorization.ACLAuthorizationPolicy` authorization policy,
    but accepts and returns callable objects (typically instances of
    :class:`PrivCheck`) as principals in addition to simple principal strings.
    The current principal list `principals` is evaluated against the callable
    by calling the callable with `principals` as its only argument.
    """
    def permits(self, context, principals, permission):
        """ Return an instance of
        :class:`pyramid.security.ACLAllowed` instance if the policy
        permits access, return an instance of
        :class:`pyramid.security.ACLDenied` if not."""

        acl = '<No ACL found on any object in resource lineage>'

        for location in lineage(context):
            try:
                acl = location.__acl__
            except AttributeError:
                continue

            for ace in acl:
                ace_action, ace_principal, ace_permissions = ace

                # This block is the only deviation from Pyramid's authz policy
                principal_match = False
                if hasattr(ace_principal, '__call__'):
                    if ace_principal(principals):
                        principal_match = True
                elif ace_principal in principals:
                    principal_match = True

                if principal_match:
                    if not is_nonstr_iter(ace_permissions):
                        ace_permissions = [ace_permissions]
                    if permission in ace_permissions:
                        if ace_action == Allow:
                            return ACLAllowed(ace, acl, permission,
                                              principals, location)
                        else:
                            return ACLDenied(ace, acl, permission,
                                             principals, location)

        # default deny (if no ACL in lineage at all, or if none of the
        # principals were mentioned in any ACE we found)
        return ACLDenied(
            '<default deny>',
            acl,
            permission,
            principals,
            context)


def auto_privilege_escalation(event):
    """A Pyramid event listener that calls :func:`attempt_privilege_escalation`
    if possible and necessary."""

    request = event.request

    if request.permission is None:
        # Resource is not protected by a permission
        return

    if has_permission(request.permission, request.context, request):
        # Access will be granted; all is well
        return

    attempt_privilege_escalation(request.permission, request.context, request)


def attempt_privilege_escalation(permission, context, request):
    """Try to automatically guide the user through elevating their privileges.

    If it is possible to automatically guide the user to gain the privileges
    needed to gain the given permission in the given context, do so.  This may
    entail setting a stash for the current request then redirecting.

    """
    upgradeable = ('cred:browserid_recent', 'cred:openid_recent')

    if not could_have_permission(permission, context, request):
        return

    for altset in outstanding_principals(permission, context, request):
        if len(altset) != 1:
            continue

        principal = altset.pop()

        if principal in upgradeable:
            # Can elevate by performing a simple authentication; so set a
            # return_key and redirect to the login screen
            key = stash_post(request)
            request.session.flash("You need to re-authenticate with OpenID or "
                                  "BrowserID to complete this action",
                                  level='notice')

            location = request.route_url('account.login',
                                         _query=[('return_key', key)])
            raise HTTPSeeOther(location=location)


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

    effective = effective_principals(request)
    outstanding = []

    for p in principals:
        if hasattr(p, 'delta'):
            for pp in p.delta(effective):
                if 'auth:insecure' not in pp:  # Don't suggest reducing sec
                    outstanding.append(set(pp))
        else:
            outstanding.append(set([p]))

    return outstanding


def is_upgradeable(principal, request):
    """Helper: checks the upgradeability of PrivCheck and str principals"""
    if hasattr(principal, 'upgradeable'):
        return principal.upgradeable(effective_principals(request))
    return principal.startswith(UPGRADABLE_PRINCIPALS)


def could_have_permission(permission, context, request):
    """Returns True if the current user (``request.user``) either holds the
    `permission` in the given `context` or could hold it after
    :term:`authentication upgrade`."""

    if context is None:
        return False

    if not hasattr(context, '__acl__'):
        # XXX is this bit of convenience appropriate?
        from floof.resource import contextualize
        context = contextualize(context)

    outstanding = outstanding_principals(permission, context, request)

    if not outstanding:
        return True

    # The user can gain the permission only if there is an alternative set in
    # their outstanding_principals list of sets containing only upgradable
    # principal types.
    for altset in outstanding:
        if all(is_upgradeable(f, request) for f in altset):
            return True

    return False


def add_user_authz_methods(user, request):
    """Add the ``can`` and ``permitted`` convenience methods to the `user`"""

    from floof.resource import contextualize

    def user_can(permission, context=None):
        """Returns True if the current user can (potentially after re-auth
        and/or a settings change) have the given permission in the given
        context, else False.  context defaults to request.context."""
        if context is None:
            context = request.context
        return could_have_permission(permission, context, request)

    def user_permitted(permission, lst):
        """Filter iterable lst to include only ORM objects for which the
        request's user holds the given permission."""
        f = lambda obj: request.user.can(permission, contextualize(obj))
        return filter(f, lst)

    user.can = user_can
    user.permitted = user_permitted


def permissions_in_context(context, request):
    """Returns a list of ``(permission, allowed, upgradable)`` tuples for each
    permission defined in the ACL (``__acl__``) of the `context`.  `allowed` is
    a boolean that is True if ``request.user`` holds that permission in that
    context and `upgradeable` is a boolean that is True if `allowed` is False
    but the permission may be gained by the user by authentication upgrade
    (typically re-authentication or using cert auth)."""

    acl = getattr(context, '__acl__', None)

    if not acl:
        return []

    permissions = set()
    for action, principal, perms in acl:
        if (perms == ALL_PERMISSIONS or
                isinstance(perms, basestring) or
                not hasattr(perms, '__iter__')):
            perms = [perms]
        permissions.update(set(perms))

    results = []
    for perm in sorted(permissions):
        allowed = has_permission(perm, context, request)
        upgradeable = None
        if not allowed:
            upgradeable = could_have_permission(perm, context, request)
        results.append((perm, allowed, upgradeable))

    return results


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
