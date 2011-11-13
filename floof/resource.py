"""
This module supports the ``floof`` resource tree.

As ``floof`` uses URL Dispatch, the resource tree provides only authorization
information, and authorization is the focus of this module.

"""
from pyramid.security import Allow, Deny
from pyramid.security import Authenticated, Everyone

from floof.model import Comment

ROOT_ACL = (
    (Deny, 'banned:interact_with_others', (
        'art.rate',
        'comments.add',
        'tags.add',
    )),

    (Allow, Authenticated, '__authenticated__'),

    (Allow, 'role:user', (
        'art.upload', 'art.rate',
        'comments.add',
        'tags.add', 'tags.remove',
    )),

    (Allow, 'trusted_for:auth', (
        'auth.method', 'auth.certificates', 'auth.openid')),

    (Allow, 'trusted_for:admin', ('admin.view')),
)
"""The root ACL attached to instances of :class:`FloofRoot`.

This ACL defines the base, generic permissions that apply in the absence of an
ORM object with more specific or nuanced principal -> permission mappings.
"""

ORM_ACLS = {
    Comment: lambda ormobj: (
        (Allow, 'user:{0}'.format(ormobj.author_user_id), (
            'comment.delete',
        )),
        (Allow, 'trusted_for:admin', (
            'comment.delete',
            'comment.edit',
        )),
    ),
}
"""A mapping from a subset of ORM classes to factory functions that, called
with an ORM object of that class, will return a Pyramid ACL appropriate for
application to that object.

This constant essentially defines the ACLs that should be applied to ORM
objects by :func:`contextualize`.
"""


class FloofRoot(dict):
    """Root element of the Floof context tree.

    The ``__acl__`` attribute of this class is :const:`ROOT_ACL`.

    At present, the option request parameter is ignored.

    """
    __name__ = ''
    __parent__ = None
    __acl__ = ROOT_ACL

    def __init__(self, request=None):
        pass

    def __repr__(self):
        tmpl = "<FloofContext '{cls}' ( Name: '{name}'; Parent: '{parent}' )>"
        return tmpl.format(cls=self.__class__.__name__, name=self.__name__,
                           parent=self.__parent__)


def contextualize(ormobj, name=None, root=None):
    """Attaches an ORM object to a makeshift resource tree.

    `ormobj` is attached to the tree by adding appropriate attributes.  The
    tree is only guarnteed to contain those elements required to successfully
    preform ACL authorization on the object.  If `ormobj` already has an
    ``__acl__`` or ``__parent__`` attribute, then it is returned immediately
    and without modification.

    Currently all objects are shoved into a fresh two-member tree with the
    modifierd `ormobj` as the only leaf and an instance of :class:`FloofRoot`
    as the root.

    Typically, this function is used to wrap ORM objects as part of a URL
    Dispatch route factory.  Note that, as the returned object is used as both
    the context and the ``request.root``, this gives rise to the peculiar state
    of affairs where ``request.root`` does not point to the root of the context
    tree, but to the ORM object `ormobj`.  This behaviour is expected and
    should not cause any problems with
    :class:`pyramid.authorization.ACLAuthorizationPolicy`.

    Parameters:

       `ormobj`
          The ORM object to "contextualize", that is, to add an ACL to (if
          applicable) and to place an an appropriate resource tree.

       `name`
          Defaults to the concatenation of the class name of `ormobj` with
          either the value of ``ormobj.id`` or, failing that, ``id(ormobj)``.
          The ``__name__`` attribute that will be added ot `ormobj`.

       `root`
          Defaults to ``FloofRoot()``. The object to use as the root of the
          context tree into which `ormobj` will be placed.

    """
    if hasattr(ormobj, '__acl__') or hasattr(ormobj, '__parent__'):
        return ormobj

    if name is None:
        objid = getattr(ormobj, 'id', id(ormobj))
        name = ormobj.__class__.__name__ + ':' + str(objid)

    parent = root or FloofRoot()
    parent[name] = ormobj
    ormobj.__name__ = name
    ormobj.__parent__ = parent

    ormcls = ormobj.__class__
    if ormcls in ORM_ACLS:
        ormobj.__acl__ = ORM_ACLS[ormcls](ormobj)

    return ormobj
