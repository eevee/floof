import binascii
import datetime
import logging
import pytz

from sqlalchemy.orm.exc import NoResultFound

from floof import model

log = logging.getLogger(__name__)


## Generic OAuth2


# Assuming len(charset) == 62
OAUTH2_GRANT_CODE_LEN = 27  # > 160 bits
OAUTH2_ACCESS_TOKEN_LEN = 27  # > 160 bits
OAUTH2_REFRESH_TOKEN_LEN = 43  # > 256 bits


class OAuth2Error(Exception):
    name = 'unspecified'
    status_code = 400

    @property
    def status(self):
        return self.status_code

class InvalidRequestError(OAuth2Error):
    name = 'invalid_request'
class UnacceptableError(OAuth2Error):
    name = 'invalid_request'
    status_code = 406
class InvalidClientError(OAuth2Error):
    name = 'invalid_client'
    status_code = 401
class InvalidGrantError(OAuth2Error):
    name = 'invalid_grant'
class UnauthorizedClientError(OAuth2Error):
    name = 'unauthorized_client'
class UnsupportedGrantTypeError(OAuth2Error):
    name = 'unsupported_grant_type'
class InvalidScopeError(OAuth2Error):
    name = 'invalid_scope'
class AccessDeniedError(OAuth2Error):
    name = 'access_denied'
class UnsupportedResponseTypeError(OAuth2Error):
    name = 'unsupported_response_type'
class UnauthorizedRedirectURIError(OAuth2Error):
    # Non-standard error type; only use internally
    name = 'unauthorized_redirect'
class UnsupportedTokenTypeError(OAuth2Error):
    name = 'unsupported_token_type'
class InvalidTokenError(OAuth2Error):
    name = 'invalid_token'


def error_to_dict(error):
    ret = {'error': error.name}
    if error.args and error.args[0]:
        ret.update({'error_description': error.args[0]})
    return ret


def const_equal(x, y):
    """(Best effort) constant-time string equality tester."""

    if len(x) != len(y):
        return False

    res = 0
    for a, b in zip(x, y):
        res |= ord(a) ^ ord(b)
    return res == 0


def parse_client_authorization(request):
    """Returns the client_identifier and client_secret from a request.

    Only supports HTTP Basic Authorizaion.  That is, Authorization headers of
    the form:

    Authorization: Basic Base64(identifier + ":" + secret)

    or

    Authorization: Basic Base64(identifier)

    """
    try:
        # On access, request.authorization may return None, return a 2-tuple,
        # or throw ValueError
        auth = request.authorization
        if not auth:
            raise InvalidClientError(
                'Client identification/authentication is required')
        authtype, authblob = auth
    except ValueError:
        raise InvalidClientError(
            "Client identification/authentication is malformed; must be "
            "'Authorization: auth-scheme auth-param'")

    if authtype.lower() != 'basic':
        raise InvalidClientError(
            'Only the Basic authentication scheme is supported for client '
            'identification/authentication')

    crederrmsg = (
        "Client identification/authentication is malformed; auth-param must "
        "be base64(identifier) or base64(identifier + ':' + secret) and the "
        "identifer and secret must be encoded in UTF-8"
    )

    try:
        credentials = authblob.decode('base64').strip()
        if ':' in credentials:
            identifier, secret = credentials.split(':')
        else:
            identifier, secret = credentials, None
    except (ValueError, binascii.Error):
        raise InvalidClientError(crederrmsg)

    # Coerce credentials into unicode
    try:
        identifier = identifier.decode('utf-8')
        if secret is not None:
            secret = secret.decode('utf-8')
    except UnicodeDecodeError:
        raise InvalidClientError(crederrmsg)

    return identifier, secret


def expires_in(seconds):
    """Returns a datetime <seconds> in the future."""
    now = datetime.datetime.now(pytz.utc)
    return now + datetime.timedelta(seconds=seconds)


def may_get(source, name, default=None):
    # XXX: How does this handle '?foor&bar' querys? (should reject as invalid)
    values = source.getall(name)
    if len(values) > 1:
        raise InvalidRequestError(
            'Parameters must not be included more than once')
    return values[0] if values else default


def must_get(source, name):
    value = may_get(source, name)
    # "Parameters sent without a value MUST be treated as if they were
    # omitted from the request", hence 'not' rather than 'is None'
    if not value:
        raise InvalidRequestError(
            'Must include the {0} parameter'.format(name))
    return value


def ranges_to_chars(ranges):
    chars = []
    for low, high in ranges:
        chars.extend([unichr(i) for i in xrange(low, high + 1)])
    return chars


# scope-token = 1*( %x21 / %x23-5B / %x5D-7E )
scope_chars = ((0x21, 0x21), (0x23, 0x5b), (0x5d, 0x7e))
scope_chars = set(ranges_to_chars(scope_chars)) | set(u' ')
"""Per `section 3.3`_ of the OAuth 2.0 draft#28 spec.

.. _`section 3.3`:_https://tools.ietf.org/html/draft-ietf-oauth-v2-28#section-3.3
"""


def parse_scope(scope, available_scopes=None):
    """Parse scope string and return a list of scopes.

    Per `section 3.3`_ of the OAuth 2.0 draft spec.

    A list of space-delimited, case sensitive strings.  While a list is
    returned, their order does not matter.

    .. _`section 3.3`:_https://tools.ietf.org/html/draft-ietf-oauth-v2-28#section-3.3

    """
    if not scope:
        return []

    # Check scope for invalid characters
    if not set(scope) <= scope_chars:
        raise InvalidScopeError('Invalid characters in scope string')

    # scope = scope-token *( SP scope-token )
    scopes = scope.split(u' ')

    if scope.startswith(u' ') or scope.endswith(u' ') or not all(scopes):
        # XXX: Should extra spaces just be silently dropped?
        raise InvalidScopeError('Multiple spaces in scope string')

    # Unique-ify
    scopes = list(set(scopes))

    if available_scopes is None:
        available_scopes = all_scopes()

    if any(s for s in scopes if s not in available_scopes):
        raise InvalidScopeError('Available scopes are: {0}'
                                .format(' '.join(available_scopes)))

    return sorted(scopes)


## Floof-specific


def all_scopes():
    scopes = model.session.query(model.Scope).all()
    return [s.name for s in scopes]


def get_client(identifier):
    if not identifier:
        raise InvalidClientError(
            "Client identification/authentication must include a client ID")

    q = model.session.query(model.OAuth2Client).filter_by(identifier=identifier)

    try:
        client = q.one()
    except NoResultFound:
        # I assume that client enumeration is not a concern
        raise InvalidClientError('No such client')

    return client


def get_confidential_client(identifier, secret):
    """Identify, authenticate & return a confidential client.

    The passed secret must match the client's secret.

    On success returns a :class:`floof.model.OAuth2Client` ORM object.
    On failure raises :exc:`InvalidClientError` with an appropriate error
    message.

    """
    if not secret:
        raise InvalidClientError(
            'Confidential clients must provide a client secret; public '
            'clients must omit the secret and separating colon')

    client = get_client(identifier)

    if client.auth_type != u'confidential':
        raise InvalidClientError(
            'Public clients must omit any secret')

    if not const_equal(client.secret, secret):
        raise InvalidClientError(
            'No such confidential client or incorrect client secret; public '
            'clients must omit any secret')

    return client


def get_public_client(identifier):
    """Identify & return a public client.

    On success returns a :class:`floof.model.OAuth2Client` ORM object.
    On failure raises :exc:`InvalidClientError` with an appropriate error
    message.

    """
    client = get_client(identifier)

    if client.auth_type != u'public':
        raise InvalidClientError(
            'Confidential clients must supply their secret')

    return client


def get_redirect_uri(client, given_uri=None):
    """Returns a valid redirect_uri for the given client.

    If given_uri is unspecified, the client's default redirect_uri is returned.

    If given_uri is specified and is valid for the client, then given_uri is
    returned.

    If given_uri is specified but not valid for the client, an
    UnauthorizedRedirectURIError is raised.

    """
    if not given_uri:
        return client.redirect_uris[0]

    if given_uri not in client.redirect_uris:
        raise UnauthorizedRedirectURIError(
            'Given redirect URI does not match any registered redirect URI.')

    return given_uri


def client_from_request(request):
    # We only support authentication via Authorization header
    identifier, secret = parse_client_authorization(request)

    # Retrieve the client, authenticating confidential clients
    if secret is not None:
        return get_confidential_client(identifier, secret)
    else:
        return get_public_client(identifier)
