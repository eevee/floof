"""
This module contains functions that mostly assist with Authentication Upgrade.

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

from pyramid.security import effective_principals, has_permission
from pyramid.security import principals_allowed_by_permission

from floof.resource import contextualize

log = logging.getLogger(__name__)

UPGRADABLE_PRINCIPALS = ('auth:', 'trusted:')

TRUST_MAP = dict([
    ('trusted_for:auth', [
        ('role:user', 'auth:insecure', 'trusted:browserid_recent'),
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
    if not could_have_permission(permission, context, request):
        return

    for altset in outstanding_principals(permission, context, request):
        if len(altset) != 1:
            continue

        principal = altset.pop()

        if principal.startswith('trusted:') and principal != 'trusted:cert':
            # Can elevate by performing an OpenID authentication; so set a
            # return_key and redirect to the login screen
            from floof.lib.stash import stash_post
            from pyramid.httpexceptions import HTTPSeeOther

            key = stash_post(request)
            request.session.flash("You need to re-authenticate with OpenID or "
                                  "BrowserID to complete this action",
                                  level='notice')

            location = request.route_url('account.login', _query=[('return_key', key)])
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


def add_user_authz_methods(user, request):
    """Add the ``can`` and ``permitted`` convenience methods to the `user`"""

    def user_can(permission, context=None):
        """Returns True if the current user can (potentially after re-auth
        and/or a settings change) have the given permission in the given
        context, else False.  context defaults to request.context."""
        if context is None:
            context = request.context
        return could_have_permission(permission, context, request)

    def user_permitted(permission, lst):
        """Filter iterable lst to include only ORM objects for which the request's
        user holds the given permission."""
        f = lambda obj: request.user.can(permission, contextualize(obj))
        return filter(f, lst)

    user.can = user_can
    user.permitted = user_permitted


def permissions_in_context(context, request):
    """Returns a list of ``(permission, allowed, upgradable)`` tuples for each
    permission defined in the ACL (``__acl__``) of the `context`.  `allowed` is
    a boolean that is True if ``request.user`` holds that permission in that
    context and `upgradeable` is a Boolean that is True if `allowed` is False
    but the permission may be gained by the user by authentication upgrade
    (typically re-authentication or using cert auth)."""

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
