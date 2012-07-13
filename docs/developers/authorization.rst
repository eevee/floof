.. _section-developers-authz:

Authorization
=============

Overview
--------

Authorization in ``floof`` broadly follows the default Pyramid authorization
model.  That is, it takes a set of principals identifiers and converts them,
within a particular Pyramid `context`, to a set of permissions that are then
used to determine access to a particular Pyramid `view`.

The authorization policy used by ``floof`` is
:class:`floof.lib.authz.FloofACLAuthorizationPolicy`, which is a subclass of
the default Pyramid authorization policy
:class:`pyramid.authorization.ACLAuthorizationPolicy`.
The only difference is that
:class:`floof.lib.authz.FloofACLAuthorizationPolicy` supports the use not only
of simple string principals but also of :ref:`Complex Principals` in its
:ref:`authz-ACLs`.  Both policies use the ``__acl__`` attribute on a context
object and, if necessary, on its parent objects as the contextual ACL, which is
in turn used to perform the mapping from principal identifiers to permissions.
Parents are pointed to by an object's ``__parent__`` attribute.

In general, contexts in ``floof`` will be members of a context tree rooted at
the instance of :class:`floof.resource.FloofRoot`.


The ``floof`` Context Tree
--------------------------

As ``floof`` uses URL Dispatch as its only routing mechanism, there is no need
to maintain a full resource tree as there might be in Pyramid applications that
use Traversal for routing.  The context tree is used only for the purposes of
ACL inheritance as part of authorization with
:class:`floof.lib.authz.FloofACLAuthorizationPolicy`.  As such, small trees
that contain only those elements required for declarative authorization
purposes are generated on the fly on the routing of each request.

By default, the context of a request in ``floof`` will be an instance of
:class:`floof.resource.FloofRoot`.  However, for views that deal with
particular objects within the object-relational mapping (ORM) model, it is
useful to:

1. Return the relevant ORM object as the `context`; and
2. Attach an appropriate ACL to this object and place it within an appropriate
   resource tree.

Typically this fragment resource tree will be rooted at an instance of
:class:`floof.resource.FloofRoot`.


.. _authz-ACLs:

ACLs
----

Access Control Lists (ACLs) are defined in the `Pyramid documentation`_, and
consist of a series of Access Control Entries (ACEs).  ACEs are 3-tuples
consisting of:

1. An `action`, either :const:`pyramid.security.Allow` or
   :const:`pyramid.security.Deny`;

2. A principal identifier, which may be either a simple string principal such
   as ``role:admin`` or ``user:123``, or a `Complex Principal`_ such
   as ``PrivCheck(role='admin', user_id=123)``.

3. A sequence of permissions, again represented as strings, such as
   ``admin.view`` or ``comment.edit``.

.. _`Pyramid documentation`: http://docs.pylonsproject.org/docs/pyramid.html

Note that an ACE can only contain a single principal identifier.  To perform
authorization based on the simultaneous presence (or absence) of multiple
principal identifiers, is is necessary to use `Compound/Complex Principals`_.


.. _`Complex Principal`:

Compound/Complex Principals
---------------------------

Under the :class:`floof.lib.authz.FloofACLAuthorizationPolicy` authorization
policy, it is possible to specify a callable in place of a concrete string
principal in context ACLs.  This callable must accept the list of currently
active principals as its only argument and return True if the rules it embodies
are satisfied by the current principals and False otherwise.

Floof currently provides :class:`floof.lib.authz.PrivCheck`, instances of which
are callables that may be used as complex principals in ACLs.  Its use in the
majority of ACEs (ACL entries) is encouraged since the introduction of `OAuth`
as it automatically handles the exclusion of OAuth clients that do not hold
the requisite scope for an action and their complete exclusion when an
acceptable scope is not specified.


Dangers of OAuth Integration
----------------------------

At present, OAuth clients authenticate and are authorized via the same security
framework as web browsers.  As OAuth clients act on behalf of users, they are
granted the ``user:nnn`` principal and the user's ``role:xxx`` principal.
However, rather than automatically holding the same privileges as the end-user,
an OAuth client's powers must be limited to the specific scopes previously
granted by the end-user.  Thus, unlike the case of a "full" web browser
session, these principals represent the maximum possible privilege of the
end-user rather than the privilege that the OAuth client should hold.  

This situation is awkward to express using only a single simple string
principal per ACL entry.  Unless specifically denied elsewhere, any ACL entry
that grants a permission to a simple string principal will also grant that
permission to all OAuth clients acting for the end-user, regardless of whether
the end-user has knowingly granted it permission (in the form of a scope).

This means that every ACL entry with :const:`pyramid.security.Allow` should use
a compound/complex principal helper such as :class:`floof.lib.authz.PrivCheck`
as its principal unless OAuth clients have been explicitly blocked by a
``(Deny, 'cred:oauth', ALL_PERMISSIONS)`` or similar entry earlier in the same
ACL.  Note that so denying OAuth clients in ACLs further up the resource tree
is ineffective as the ``Allow`` entries in the lower ACLs will override them.


API
---

``floof.resource``
^^^^^^^^^^^^^^^^^^

.. automodule:: floof.resource
   :members:


``pyramid.authorization``
^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: pyramid.authorization
   :members:


``floof.lib.authz``
^^^^^^^^^^^^^^^^^^^

.. automodule:: floof.lib.authz
   :members:
