# encoding: utf8
import logging

from pyramid import httpexceptions
from pyramid.view import view_config

from floof.app import NoCookiesError
from floof.lib.auth import auth_actions
from floof.lib.auth import outstanding_principals

log = logging.getLogger(__name__)

def _error_view(context, request, default_message, status=None,
                image=None, outstanding_principals=None):

    status = status or getattr(context, 'status', None) or 500
    request.response.status = status

    if len(context.args) and context.args[0]:
        message = context.args[0]
    else:
        message = default_message

    return {
        'http_status': status,
        'message': message,
        'outstanding_principals': outstanding_principals,
        'auth_actions': auth_actions,
    }

@view_config(
    context=httpexceptions.HTTPBadRequest,
    renderer='error.mako')
def error400(context, request):
    return _error_view(context, request,
        default_message="I'm afraid I can't let you do that")

@view_config(
    context=httpexceptions.HTTPForbidden,
    renderer='error.mako')
def error403(context, request):
    outstanding = None

    if request.user.can(request.permission):
        from floof.lib.auth import UPGRADABLE_PRINCIPALS
        all_outstanding = outstanding_principals(
                request.permission, request.context, request)
        outstanding = []
        for altset in all_outstanding:
            f = lambda x: x.startswith(UPGRADABLE_PRINCIPALS)
            if all(map(f, altset)):
                outstanding.append(altset)

    return _error_view(context, request,
                       default_message="I'm afraid I can't let you do that",
                       outstanding_principals=outstanding)

@view_config(
    context=httpexceptions.HTTPNotFound,
    renderer='error.mako')
def error404(context, request):
    # XXX this can probably be improved
    return _error_view(context, request,
        default_message=u"No such number // no such zone  ♪")


@view_config(
    context=NoCookiesError,
    renderer='error.mako')
def no_cookies_error(context, request):
    msg = ("It appears cookies may be disabled in your browser.  "
           "Unfortunately, this site requires cookies in order for you to log "
           "in and to perform any actions such as submitting art or changing "
           "your personal settings.  To enable cookies, please refer to your "
           "browser's instructions on privacy or security settings.")

    # XXX 409 Conflict "This code is only allowed in situations where it is
    # expected that the user might be able to resolve the conflict and resubmit
    # the request". Is it the most appropriate code here? Or should we use 400?
    return _error_view(context, request, msg, status=409,
                       image='cookie--exclamation')
