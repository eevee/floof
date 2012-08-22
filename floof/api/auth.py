# encoding: utf-8
import logging

from hashlib import sha512

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated, Everyone
from sqlalchemy.orm.exc import NoResultFound
from zope.interface import implements

from floof import model
from floof.lib.oauth import InvalidRequestError, InvalidTokenError

log = logging.getLogger(__name__)

BASIC_SCHEME_ROUTES = (
    'oauth2.token',
    'oauth2.revoke',
)


class FloofAPIAuthnPolicy(object):
    """Pyramid style authentication policy for OAuth2."""

    implements(IAuthenticationPolicy)

    def authenticated_userid(self, request):
        token = request.token
        return token.user_id if token else None

    def unauthenticated_userid(self, request):
        raise NotImplementedError

    def effective_principals(self, request):
        """Returns the list of 'effective' :term:`principal` identifiers for
        the request."""

        principals = set([Everyone])

        token = request.token
        if not token:
            return principals

        principals.add(Authenticated)
        principals.add('client:' + str(token.client_id))
        principals.add('user:' + str(token.user_id))

        principals.update(u'scope:' + s for s in token.scopes)
        # Each scope and role should have both a generic instance and one that
        # ties it to a particular user; generally only one of the two will be
        # used by ACLs, but generating both for all is easier
        principals.update(u'scope:{0}:{1}'.format(s, token.user_id)
                          for s in token.scopes)

        return principals

    def remember(self, request, user):
        # Should this be used to send the token to the client?
        # Seems like it would be easier just to keep that in the token endpoint
        return NotImplementedError

    def forget(self, request):
        # Should this invalidate the access token?
        return NotImplementedError


def token_from_request(request):
    """Extracts and validates OAuth2 accress tokens.

    On success, returns the validated access token ORM object.
    On failure, raises an error derived from
    :exc:`floof.lib.oauth.OAuth2Error`

    """
    if request.matched_route.name in BASIC_SCHEME_ROUTES:
        return

    token_type, token_id = get_access_token_id(request)
    if token_id is None:
        return

    token = sha512(token_id).hexdigest()
    # TODO: Optimize eagerloading
    q = model.session.query(model.OAuth2AccessToken) \
        .filter_by(token=token)

    try:
        access_token = q.one()
    except NoResultFound:
        raise InvalidTokenError(
            'The given access token is not on record.')

    if access_token.expired:
        raise InvalidTokenError(
            'The given access token has expired.')

    if access_token.type != token_type:
        raise InvalidTokenError(
            "Asserted access token type '{0}' must match the actual token "
            "type '{1}'.".format(token_type, access_token.type))

    return access_token


def get_access_token_id(request, valid_schemes=['bearer']):
    """Extract an OAuth access token from a request.

    Returns an (authtype, token) tuple, where authtype is in valid_schemes.

    Raises :exc:`floof.lib.oauth.InvalidRequestError` if a malformed
    Authorization header is encountered or if an unsupported Authorization
    scheme is provided.

    """
    try:
        if not request.authorization:
            return None, None
        authtype, token = request.authorization
    except ValueError:
        raise InvalidRequestError(
            'The Authorization header must be of the form: '
            'Authorization: Bearer TOKEN.')

    if not authtype or not token:
        raise InvalidRequestError(
            'The Authorization header must be of the form: '
            'Authorization: Bearer TOKEN.')

    authtype = authtype.lower()

    if valid_schemes and authtype not in valid_schemes:
        raise InvalidRequestError(
            "The only supported Authorization schemes are: {0}"
            .format(valid_schemes))

    # It's hard to get a strong guarantee that the bearer token came over TLS;
    # this is a best-effort deal
    if request.scheme != 'https':
        log.warning(
            'Recieved a bearer token apparently without HTTPS; ignoring it')
        return None, None

    return authtype, token
