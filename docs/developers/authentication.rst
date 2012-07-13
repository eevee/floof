.. _section-developers-authn:

Authentication
==============

Overview
--------

Authentication in ``floof`` aims to provide the end user with both flexibility
and a reasonably high standard of security.

Three primary mechanisms of authentication are supported:

1. BrowserID
2. OpenID
3. TLS Client Certificates

It is expected that most users will use only BrowserID, with some using OpenID
and just administrators and a minority of power users employing client
certificates.

In ``floof``, the scope of 'authentication' runs from the interpretation of
`credential tokens` to the assignment of :term:`principal` identifiers.  These
principal identifiers are then used by :ref:`section-developers-authz`
components to assign permissions within a particular :term:`context`.

Note that the actual authentication of credentials, such as the verification of
an X.509 client certificate or the OpenID authentication process, are beyond
the scope of this documentation section.  Instead of considering raw
credentials such as an X.509 certificate or usernames and passwords, this
section assumes that previous successful validations of such credentials have
been stored or are passed on each request as `credential tokens`, such as the
serial of an X.509 certificate or an OpenID URL.


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

1. A client certificate serial is passed via HTTP header (currently
   ``X-Floof-SSL-Client-Serial``) from the front-end HTTP server (if the client
   presented a valid certificate within the context of the current TLS
   session);

2. An OAuth `Bearer token`_ may be passed via the ``Authorization`` HTTP
   header; and

3. The URL and timestamp of the most recent successful OpenID validation and
   the email address and timestamp of the most recent successful BrowserID
   validation are stored in the Pyramid session.

.. _`Bearer token`: https://tools.ietf.org/html/draft-ietf-oauth-v2-bearer-20


Resolving Identity
^^^^^^^^^^^^^^^^^^

Each credential token may be resolved to exactly one user identity.  However,
to resolve the user within the context of a given request it is necessary to
consider the possibility of multiple credentials disagreeing on the user's
identity.  To avoid such conflicts, the credential tokens are inspected and
resolved to a user identity in the following order:

1. TLS Client Certificate
2. OpenID
3. BrowserID
4. OAuth

Once one authentication mechanism has resolved a credential token to a user,
subsequent mechanisms that resolve to a conflicting user will be ignored and
the conflicting credential tokens will be purged, if possible.

At this point, the authentication flow will know the request's authenticated
user (if any) and the valid mechanisms on which their authentication status is
based.


Retrieving Concrete Principal Identifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are five types of concrete principal identifiers:

1. User identifiers, prefixed with ``user:``, that contain simply the user ID
   of the active user, modelled as a principal identifier for convenience.

2. Role identifiers, prefixed with ``role:``.  A user holds a single role,
   either assigned by an administrator or defaulting to ``role:user``.  They
   represent the static privilege level of the user.  e.g.:

   -  ``role:admin``
   -  ``role:moderator``
   -  ``role:user``

3. Authentication mechanism and status identifiers, currently prefixed with
   ``cred:``.  These indicate the currently valid credential tokens and
   their properties, such as whether a BrowserID or OpenID verification was
   preformed 'recently'.  e.g.:

   -  ``cred:cert``
   -  ``cred:openid``
   -  ``cred:openid_recent``
   -  ``cred:browserid``
   -  ``cred:browserid_recent``
   -  ``cred:oauth``

4. Authentication setting identifiers, prefixed with ``auth:``.  These indicate
   properties of a user's authentication settings, such as whether a
   client certificate is required for sensitive operations.  e.g.:

   -  ``auth:insecure``
   -  ``auth:secure``

5. Scope identifiers, prefixed with ``scope:``.  These are granted to OAuth
   clients and represent the extent of access granted by the end-user.  They
   should not provide access above that permitted to the underlying/effective
   end-user, but that is a matter for :ref:`section-developers-authz` to
   enforce.  e.g.:

   -  ``scope:art``
   -  ``scope:comment``

Note that the principal identifiers are treated as flags and are included into
a request's list in an additive fashion.  For instance, if a user has recently
performed an OpenID credential verification, their request will include both
the ``cred:openid_recent`` and ``cred:openid`` principal identifiers.


.. _authn-complex-principals:

Compound/Complex Principal Identifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Principals as resolved by the above mechanism are represented as simple
strings, all of which apply equally to the request as flags and do not
interact with each other.

However, it is desirable in some circumstances to express the result of
interactions or combinations of these simple, concrete, string principals.  The
solution (covered in detail in :ref:`section-developers-authz`) is complex
pseudo-principals that are actually callables accepting a list of active
principals and returning True or False.

This provides a more manageable way to grant a permission based on common or
meaningful combinations of other principal identifiers.  For instance, the
presence of ``cred:oauth`` should have the unusual effect of actually limiting
granted permissions unless the relevant ``scope:*`` principals are also held by
the request.


Authorization
^^^^^^^^^^^^^

These and other principal identifiers are based purely on a request's
credential tokens, that is, on a user's authentication status, and are the same
across all contexts.  To actually be permitted to perform restricted actions
requires the translation of these principal identifiers into into
`permissions`.  This translation depends on the relevant Pyramid context of the
action or its target, and is covered in detail under
:ref:`section-developers-authz`.


API
---

The following is documentation of the authentication components of ``floof``.

The :class:`floof.lib.authn.Authenticizer` class is responsible for gathering
and interpreting credential tokens, resolving them to a single user, and
maintaining an authentication state free of identity conflicts.
:class:`floof.app.FloofRequest` attaches an instance of this class to itself as
its ``auth`` attribute, so the current request's Authenticizer should always be
retrievable from ``request.auth``.

The :class:`floof.lib.authn.FloofAuthnPolicy` implements the Pyramid
Authentication Policy interface (to an approximation) and is responsible for
determining the principal identifiers applicable to a particular request, given
the authenticated user and information on how the user was authenticated and on
the user's authentication settings.


``floof.lib.authn``
^^^^^^^^^^^^^^^^^^^

.. automodule:: floof.lib.authn
   :members:
