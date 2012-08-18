"""
This module supports the ``floof`` resource tree.

As ``floof`` uses URL Dispatch, the resource tree provides only authorization
information, and authorization is the focus of this module.

"""
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow, Deny
from pyramid.security import Authenticated, Everyone


class ORMContext(dict):
    """A node in floof's context tree.

    For the convenience of :func:``contextualize`` the "tree" really is just
    a chain (it has only one leaf).  It is expected that the chain will be
    built from the leaf ORM object up to the root.  The constructor will
    attempt to create this chain automatically.

    If we ever use traversal for more than authorization, this will likely
    change.

    Child classes may override :attr:`parent_class` with another ORMContext
    class to indicate that that context should be used as its immediate parent,
    rather than the root context.  Child classes that do so must also override
    :meth:``get_parent_ormobj``, which must return the ORM object to which the
    :attr:`parent_class` should be applied.  In the case that the appropriate
    parent class depends on the particular ORM object, simply make the
    :attr:``parent_class`` a property getter.

    """
    parent_class = None
    __acl__ = []

    def __init__(self, ormobj, name=None, root=None):
        self.ormobj = ormobj

        # Set name
        if name is None:
            default = id(self.ormobj if self.ormobj is not None else self)
            objid = getattr(self.ormobj, 'id', default)
            name = self.ormobj.__class__.__name__ + ':' + str(objid)
        self.__name__ = name

        # Set parent, potentially recursing
        if self.parent_class:
            parent_ormobj = self.get_parent_ormobj()
            self.__parent__ = self.parent_class(parent_ormobj, root=root)
        else:
            self.__parent__ = root or FloofRoot()

        # Set parent's child
        self.__parent__[name] = self

    def __repr__(self):
        tmpl = "<FloofContext '{cls}' ( Name: '{name}'; Parent: '{parent}' )>"
        return tmpl.format(cls=self.__class__.__name__, name=self.__name__,
                           parent=self.__parent__)

    def get_parent_ormobj(self):
        raise NotImplementedError


class FloofRoot(ORMContext):
    """Root element of the Floof context tree.

    The ``__acl__`` attribute of this class defines the base, generic
    permissions that apply in the absence of an ORM object with more specific
    or nuanced principal -> permission mappings.

    At present, the optional request parameter is ignored.

    """
    __acl__ = [
        (Allow, 'trusted_for:admin', ALL_PERMISSIONS),

        (Deny, 'banned:interact_with_others', (
            'art.rate',
            'comments.add',
            'tags.add',
        )),

        (Allow, Authenticated, '__authenticated__'),

        (Allow, 'role:user', (
            'art.upload', 'art.rate',
            'comments.add',
            'oauth.clients.add',  # XXX: should this require trusted_for:auth?
            'tags.add', 'tags.remove',
        )),

        (Allow, 'trusted_for:auth', (
            'auth.method', 'auth.certificates', 'auth.openid',
            'auth.browserid')),
    ]

    def __init__(self, request=None):
        self.__name__ = ''
        self.__parent__ = None


class ResourceCtx(ORMContext):
    pass


class DiscussionCtx(ORMContext):
    parent_class = ResourceCtx

    def get_parent_ormobj(self):
        return self.ormobj.resource


class CommentCtx(ORMContext):
    parent_class = DiscussionCtx

    def get_parent_ormobj(self):
        return self.ormobj.discussion

    @property
    def __acl__(self):
        ALL = ('comment.delete', 'comment.edit')
        comment = self.ormobj
        return [
            (Allow, 'role:user:{0}'.format(comment.author_user_id),
                ALL),
            (Allow, 'scope:comments:{0}'.format(comment.author_user_id),
                ALL),
        ]


class LabelCtx(ORMContext):
    @property
    def __acl__(self):
        label = self.ormobj
        acl = [
            (Allow, 'role:user:{0}'.format(label.user_id), ('label.view',)),
        ]
        if label.encapsulation in ('public', 'plug'):
            acl.append((Allow, Everyone, ('label.view',)))
        return acl


class OAuth2ClientCtx(ORMContext):
    @property
    def __acl__(self):
        client = self.ormobj
        acl = [
            (Allow, 'role:user:{0}'.format(client.user_id),
                ('api.oauth.edit',)),
        ]
        return acl


def contextualize(ormobj, name=None, root=None):
    """Attaches an ORM object to a makeshift resource tree.

    `ormobj` is attached to the tree by adding appropriate attributes.  The
    tree is only guaranteed to contain those elements required to successfully
    preform ACL authorization on the object.  If `ormobj` already has an
    ``__acl__`` or ``__parent__`` attribute, then it is returned immediately
    and without modification.

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
          The ``__name__`` attribute that will be added to `ormobj`.

       `root`
          Defaults to ``FloofRoot()``. The object to use as the root of the
          context tree into which `ormobj` will be placed.

    """
    # Don't re-evaluate if it looks like something tried to contextualise the
    # object before; not especially precise, though
    if hasattr(ormobj, '__acl__') or hasattr(ormobj, '__parent__'):
        return ormobj

    # XXX: Avoids a dull class->class map, but is it too hackish?
    clsname = ormobj.__class__.__name__
    ctx_cls = globals().get(clsname + 'Ctx')

    # Build the appropriate context tree
    if ctx_cls:
        ctx = ctx_cls(ormobj, name, root)
    else:
        # Lacking a more specific context, just use the root
        ctx = root or FloofRoot()

    # Get the ORM object to "hijack" the position of the context tree leaf, so
    # that the object may be used directly in authorization requests
    # XXX: Should ormobj become a child of the found leaf instead?
    ormobj.__acl__ = ctx.__acl__
    ormobj.__name__ = ctx.__name__
    ormobj.__parent__ = ctx.__parent__
    if ormobj.__parent__:
        ormobj.__parent__[ormobj.__name__] = ormobj

    return ormobj
