# encoding: utf8
import logging

from pyramid import httpexceptions
from pyramid.renderers import render_to_response
from pyramid.view import view_config

from floof.api.auth import BASIC_SCHEME_ROUTES
from floof.lib.oauth import OAuth2Error

log = logging.getLogger(__name__)


def set_www_authenticate(exc, request):
    # If there is no Authorization header, suggest an appropriate scheme
    if request.matched_route.name in BASIC_SCHEME_ROUTES:
        scheme = 'Basic'
    else:
        scheme = 'Bearer'

    # """If the client attempted to authenticate via the "Authorization"
    # request header field, the authorization server MUST respond with an
    # HTTP 401 (Unauthorized) status code, and include the
    # "WWW-Authenticate" response header field matching the authentication
    # scheme used by the client."""
    # https://tools.ietf.org/html/draft-ietf-oauth-v2-28#section-5.2
    try:
        if hasattr(request, 'authorization') and request.authorization:
            scheme, content = request.authorization
    except ValueError:
        pass

    request.response.www_authenticate = (scheme, dict(realm='api'))


def error_view(exc, request, default_message, name=None, status=None,
               scopes=None):
    if getattr(exc, 'status_code', None) == 401:
        set_www_authenticate(exc, request)

    # Preserve a previously set status code unless specifically overridden
    if request.response.status != '200 OK':
        status = status or request.response.status
    else:
        status = status or getattr(exc, 'status', None) or 500
    request.response.status = status

    # Try to grab error details from the exc
    error_name = name or getattr(exc, 'name', None) or status
    if len(exc.args) and exc.args[0]:
        message = exc.args[0]
    else:
        message = default_message

    info = {
        'error': error_name,
        'error_description': message,
    }
    print 'WWW-Authenticate:', request.response.www_authenticate
    return render_to_response('json', info, request=request)


@view_config(context=httpexceptions.HTTPBadRequest)
def error400(exc, request):
    default_msg = u"Bad request"
    return error_view(exc, request, default_msg)


@view_config(context=httpexceptions.HTTPUnauthorized)
def error401(exc, request):
    default_msg = u"Authentication is required"
    return error_view(exc, request, default_msg)


@view_config(context=httpexceptions.HTTPForbidden)
def error403(exc, request):
    if request.user:
        default_msg = u"Insufficient permissions"
    else:
        default_msg = u"Authentication is required"
    return error_view(exc, request, default_msg, scopes=None)


@view_config(context=httpexceptions.HTTPNotFound)
def error404(exc, request):
    default_msg = u"No such thing"
    return error_view(exc, request, default_msg)


@view_config(context=OAuth2Error)
def error_oauth(exc, request):
    if exc.status_code == 401:
        # "If the client attempted to authenticate via the "Authorization"
        # request header field, the authorization server MUST respond with an
        # HTTP 401 (Unauthorized) status code, and include the
        # "WWW-Authenticate" response header field matching the authentication
        # scheme used by the client."
        # https://tools.ietf.org/html/draft-ietf-oauth-v2-28#section-5.2
        # If 401 is hit without an Authorization header, suggest one using a
        # WWW-Authenticate with the (appropriate) scheme Basic
        scheme = 'Basic'
        try:
            if hasattr(request, 'authorization') and request.authorization:
                scheme, content = request.authorization
        except ValueError:
            pass
        request.response.www_authenticate = (scheme, dict(realm='token'))

    default_msg = u"OAuth error"
    return error_view(exc, request, default_msg, name=exc.name)


@view_config(context=Exception)
def error500(exc, request):
    """Catch-all error handler."""
    default_msg = u"everything is fine.  nothing is ruined._"
    return error_view(exc, request, default_msg, status='500 Server On Fire')
