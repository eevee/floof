.. _section-developers-authz:

Authorization
=============

Overview
--------

Authorization in ``floof`` follows the default Pyramid authorization model,
whereby it takes a set of principals identifiers and converts them,
within a particular Pyramid `context`, to a set of permissions that are then
used to determine access to a particular Pyramid `view`.

The Pyramid built-in authorization policy
:class:`pyramid.authorization.ACLAuthorizationPolicy` is used by ``floof``.
This policy uses the ``__acl__`` attribute on a context object and, if
necessary, on its parent objects to perform the mapping from principal
identifiers to permissions.  Parents are pointed to by an object's
``__parent__`` attribute.

In general, contexts in ``floof`` will be members of a context tree rooted at
the instance of :class:`floof.resource.FloofRoot`.


The ``floof`` Context Tree
--------------------------

As ``floof`` uses URL Dispatch as its only routing mechanism, there is no need
to maintain a full resource tree as there might be in Pyramid applications that
use Traversal for routing.  The context tree is used only for the purposes of
ACL inheritance as part of authorization with
:class:`pyramid.authorization.ACLAuthorizationPolicy`.  As such, small trees
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


ACLs
----

Access Control Lists (ACLs) are defined in the `Pyramid documentation`_, and
consist of a series of Access Control Entries (ACEs).  ACEs are 3-tuples
consisting of:

1. An `action`, either :const:`pyramid.security.Allow` or
   :const:`pyramid.security.Deny`;

2. A principal identifier, which is a string such as ``role:admin`` or
   ``user:123``; and

3. A series of permissions, again represented as strings, such as
   ``admin.view`` or ``comment.edit``.

.. _`Pyramid documentation`: http://docs.pylonsproject.org/docs/pyramid.html

Note that an ACE can only contain a single principal identifier.  To perform
authorization based on the simultaneous presence of multiple principal
identifiers, see :ref:`authn-derived-principals`.


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
