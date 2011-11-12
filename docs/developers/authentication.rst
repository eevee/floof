.. _section-developers-authn:

Authentication
==============

Overview
--------

Authentication in ``floof`` aims to provide the end user with both flexibility
and a reasonably high standard of security.

Two primary mechanisms of authentication are supported:

1. OpenID
2. TLS Client Certificates

It is expected that most users will use only OpenID, with just administrators
and a minority of power users employing client certificates.

In ``floof``, the scope of 'Authentication' runs from the interpretation of
credentials tokens to the assignment of :term:`principal` identifiers.  These
principal identifiers are then used by :ref:`section-developers-authz`
components to assign permissions within a particular :term:`context`.

Note that the actual authentication of credentials, such as the verification of
an X.509 client certificate or the OpenID authentication process are beyond the
scope of this documentation section.  Instead of considering raw credentials
such as an X.509 certificate or usernames and passwords, this section assumes
that previous successful validations of such credentials have been stored or
are passed on each request as `credential tokens`, such as the serial of an
X.509 certificate or an OpenID URL.


Authentication Flow
-------------------

Authentication in ``floof`` is re-evaluated on each request.  The following is
an outline of how the authentication components convert the information in a
request into an identity and a set of :term:`principal` identifiers.


Gathering Credential Tokens
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first step in the ``floof`` authentication flow is to gather the
credentials tokens present in a request.  These tokens represent the result of
a previous successful validation of raw credentials.  Typically, these will be
either:

-  Transient credential tokens provided in a request's environment variables or
   HTTP headers; or

-  Stateful credential tokens stored in a Pyramid session (bound to a request
   through a cookie).

At present:

1. A client certificate serial is passed via HTTP header from the front-end
   HTTP server (if the client presented a valid certificate within the context
   of the current TLS session); and

2. The URL and timestamp of the most recent successful OpenID validation is
   stored in the Pyramid session.


Resolving Identity
^^^^^^^^^^^^^^^^^^

Each credential token may be resolved to exactly one user identity.  However,
to resolve the user within the context of a given request it is necessary to
consider the possibility of multiple credentials disagreeing on the user's
identity.  To avoid such conflicts, the credential tokens are inspected and
resolved to a user identity in the following order:

1. TLS Client Certificate
2. OpenID

Once one authentication mechanism has resolved a credential token to a user,
subsequent mechanisms that resolve a conflicting user will be ignored and the
conflicting credential tokens will be purged, if possible.

At this point, the authentication flow will know the request's authenticated
user (if any) and the valid mechanisms on which their authentication status is
based.


Retrieving Concrete Principal Identifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are three types of concrete principal identifiers:

1. Role identifiers, prefixed with ``role:``.  These are assigned by
   administrators and are stored in their own database table, and represent
   static authorization properties of the user.  e.g.:

   -  ``role:admin``
   -  ``role:banned``
   -  ``role:user``

2. Authentication mechanism and status identifiers, currently prefixed with
   ``trusted:``.  These indicate the currently valid credential tokens and
   their properties, such as whether an OpenID verification was preformed
   'recently'.  e.g.:

   -  ``trusted:cert``
   -  ``trusted:openid``
   -  ``trusted:openid_recent``

3. Authentication setting identifiers, prefixed with ``auth:``.  These indicate
   properties of a user's authentication settings, such as whether a
   client certificate is required for sensitive operations.  e.g.:

   -  ``auth:insecure``
   -  ``auth:secure``

Note that the principal identifiers are treated as flags and are included into
a request's list in an additive fashion.  For instance, if a user has recently
performed an OpenID credential verification, their request will include both
the ``trusted:openid_recent`` and ``trusted:openid`` principal identifiers.


.. _authn-derived-principals:

Derived Principal Identifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A :term:`derived principal` identifier is added to a request based on the
presence of other, 'concrete' principal identifiers.  This provides a more
manageable way to grant a permission based on common or meaningful combinations
of other principal identifiers.

The pre-requisites for derived principal identifiers are specified by the
dictionary :const:`floof.lib.auth.TRUST_MAP`.


Authorization
^^^^^^^^^^^^^

These and other principal identifiers are based purely on a request's
credential tokens, that is, on a user's authentication status, and are the same
across all contexts.  To actually be able to perform restricted actions
requires the translation of these principal identifiers into into actual
permissions.  This translation depends on the relevant Pyramid context of the
action or its target, and is covered in detail under
:ref:`section-developers-authz`.


API
---

The following is documentation of the authentication components of ``floof``.

The :class:`floof.lib.auth.Authenticizer` class is responsible for gathering
and interpreting credential tokens, resolving them to a single user, and
maintaining an authentication state free of identity conflicts.
:class:`floof.app.FloofRequest` attaches an instance of this class to itself as
its ``auth`` attribute, so the current request's Authenticizer should always be
retrievable from ``request.auth``.

The :class:`floof.lib.auth.FloofAuthnPolicy` implements the Pyramid
Authentication Policy interface (to an approximation) and is responsible for
determining the principal identifiers applicable to a particular request, given
the authenticated user and information on how the user was authenticated and on
the user's authentication settings.


``floof.lib.auth``
^^^^^^^^^^^^^^^^^^

.. automodule:: floof.lib.auth
   :members:
