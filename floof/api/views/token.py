import logging

from hashlib import sha512

import transaction

from oauthlib.common import generate_token
from pyramid.security import effective_principals
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound

from floof import model
from floof.lib.oauth import (
    OAUTH2_ACCESS_TOKEN_LEN,
    OAUTH2_REFRESH_TOKEN_LEN,
    OAuth2Error,
    InvalidRequestError,
    UnacceptableError,
    InvalidGrantError,
    UnsupportedGrantTypeError,
    UnsupportedTokenTypeError,
    InvalidTokenError,
    client_from_request,
    error_to_dict,
    expires_in,
    get_confidential_client,
    get_public_client,
    may_get,
    must_get,
    parse_client_authorization,
    parse_scope,
)


log = logging.getLogger(__name__)


ACCESS_EXPIRY_PERIOD = 60 * 30

GRANT_TYPES = (
    'authorization_code',
    'refresh_token',
)


@view_config(
    route_name='oauth2.token',
    renderer='json')
@view_config(
    route_name='oauth2.revoke',
    renderer='json')
def oauth2_token_method_error(request):
    request.response.status = 400
    return dict(
        error='invalid_request',
        error_description=(
            'The OAuth2 token and revocation endpoints accept only POST '
            'requests'),
    )


def validate_and_authenticate(request):
    # We only support JSON responses
    if not 'application/json' in request.accept:
        raise UnacceptableError('The client must accept application/json')

    # It's hard to get a strong guarantee that the token request came over TLS;
    # this is a best-effort deal
    if request.scheme != 'https':
        raise InvalidRequestError(
            'The token endpoint must be accessed over TLS')

    # Retrieve the client, authenticating confidential clients
    client = client_from_request(request)

    # The rest of the request should be urlencoded in the body
    content_type = 'application/x-www-form-urlencoded'
    if request.content_type != content_type:
        raise InvalidRequestError(
            "The Content-Type must be '{0}'".format(content_type))

    return client


@view_config(
    route_name='oauth2.token',
    request_method='POST',
    renderer='json',
    http_cache=0)
def token_endpoint(request):
    """Access Token Request endpoint."""

    # TODO: Bruteforce deterrance?

    client = validate_and_authenticate(request)

    # Big ol' grant switch; must:
    # 1. Validate the grant;
    # 2. Determine the authorizing user; and
    # 3. Determine the issued (= permitted & requested) scopes.

    grant_type = must_get(request.POST, 'grant_type')
    refresh_token_ref = None

    if grant_type == 'authorization_code':
        issue_refresh = True

        code = must_get(request.POST, 'code')
        redirect_uri = may_get(request.POST, 'redirect_uri')

        # Retrieve auth code; ensure it was issued to the requesting client
        # XXX: I assume that timing attacks are mitigated by storing only the
        # hash, since discovering the hash of a random 160-bit string should be
        # worthless; still, we may wish to revisit this later
        q = model.session.query(model.OAuth2Grant)
        q = q.filter(
            model.OAuth2Grant.client == client,
            model.OAuth2Grant.expires > model.now(),
            model.OAuth2Grant.code == sha512(code).hexdigest(),
        )
        try:
            grant = q.one()
        except NoResultFound:
            raise InvalidGrantError(
                'Authorization code does not exist, has expired, or was '
                'issued to another client')

        # Validate the authorization code grant
        if grant.redirect_uri_supplied and not redirect_uri:
            raise InvalidGrantError(
                'redirect_uri parameter must be supplied if it was supplied '
                'in the authorization request')
        if redirect_uri and grant.redirect_uri != redirect_uri:
            raise InvalidGrantError(
                'redirect_uri parameter must be identical to the redirect_uri '
                'supplied in the authorization request')

        # Guard aggressively against grant re-use -- it may indicate that a
        # third party stole the grant and (if they presented it first) were
        # issued with tokens, so invalidate any associated tokens
        if grant.redeemed:
            if grant.refresh_token:
                # Associated access tokens are auto deleted via cascade
                model.session.delete(grant.refresh_token)
            model.session.delete(grant)
            # Throwing an error rolls back uncommited transactions, so commit
            transaction.commit()
            raise InvalidGrantError(
                'This authorization code has already been redeemed.  For '
                'security reasons, the associated refresh and access tokens '
                'have now been revoked')

        user = grant.user
        scopes = grant.scopes

    elif grant_type == 'refresh_token':
        issue_refresh = False

        token = must_get(request.POST, 'refresh_token')
        scopes = parse_scope(may_get(request.POST, 'scope'))

        # Retrieve refresh token; ensure it was issued to the requesting client
        # XXX: See caveat about timing attacks in authorization_code flow above
        q = model.session.query(model.OAuth2RefreshToken)
        q = q.filter_by(client=client, token=sha512(token).hexdigest())
        try:
            refresh_token = q.one()
        except NoResultFound:
            raise InvalidGrantError(
                'Refresh token does not exist, was revoked, or was issued to '
                'another client')

        user = refresh_token.user

        if scopes:
            # Restrict access token scopes to those granted to the refresh
            # token
            scopes = [s for s in scopes
                      if s in refresh_token.scopes]
        else:
            # No specified scopes on refresh means same scope as refresh token
            # Deepcopy to avoid stale association proxy errors later
            scopes = list(refresh_token.scopes)

        refresh_token_ref = refresh_token

    else:
        raise UnsupportedGrantTypeError(
            'This endpoint only supports the following grant types: {0}'
            .format(','.join(GRANT_TYPES)))

    ret = dict()

    # Refresh token
    if issue_refresh:
        # TODO: (Optional) rotate refresh token on each refresh
        token = generate_token(OAUTH2_REFRESH_TOKEN_LEN)
        new_refresh_token = model.OAuth2RefreshToken(
            client=client,
            token=sha512(token).hexdigest(),
            user=user,
            scopes=scopes,
        )
        model.session.add(new_refresh_token)
        ret.update({'refresh_token': token})
        refresh_token_ref = new_refresh_token

        if grant_type == 'authorization_code':
            grant.refresh_token = new_refresh_token

    # Access token
    token = generate_token(OAUTH2_ACCESS_TOKEN_LEN)
    access_token = model.OAuth2AccessToken(
        client=client,
        token=sha512(token).hexdigest(),
        expires=expires_in(ACCESS_EXPIRY_PERIOD),
        user=user,
        scopes=scopes,
    )
    if refresh_token_ref:
        refresh_token_ref.access_tokens.append(access_token)

    model.session.add(access_token)
    ret.update(dict(
        access_token=token,
        token_type='Bearer',
        expires_in=ACCESS_EXPIRY_PERIOD,
        scope=' '.join(scopes),
    ))

    return ret


@view_config(
    route_name='whoami',
    request_method='GET',
    renderer='json',
    http_cache=0)
def whoami_endpoint(request):
    return dict(
        user=getattr(request.user, 'name', None),
        principals=sorted(list(effective_principals(request))),
    )


@view_config(
    route_name='oauth2.revoke',
    request_method='POST',
    renderer='json',
    http_cache=0)
def revocation_endpoint(request):
    """Token Revocation endpoint."""

    # TODO: Bruteforce deterrance?

    client = validate_and_authenticate(request)

    token = must_get(request.POST, 'token')

    if len(token) == OAUTH2_REFRESH_TOKEN_LEN:
        cls = model.OAuth2RefreshToken
    elif len(token) == OAUTH2_ACCESS_TOKEN_LEN:
        cls = model.OAuth2AccessToken
    else:
        raise UnsupportedTokenTypeError(
            'Only refresh and access token revocation is supported.  Refresh '
            'tokens must be {0} characters long; access tokens must be {1} '
            'characters long'
            .format(OAUTH2_REFRESH_TOKEN_LEN, OAUTH2_ACCESS_TOKEN_LEN))

    q = model.session.query(cls)
    q = q.filter_by(client=client, token=sha512(token).hexdigest())

    try:
        token_obj = q.one()
    except NoResultFound:
        raise InvalidTokenError(
            'No such token or token not issued to this client')

    model.session.delete(token_obj)

    return dict()
