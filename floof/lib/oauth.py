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
