# encoding: utf8
import logging

from pyramid import httpexceptions
from pyramid.view import view_config

log = logging.getLogger(__name__)

def _error_view(context, request, default_message, image=None):
    request.response.status = context.status

    if context.args[0]:
        message = context.args[0]
    else:
        message = default_message

    return {
        'http_status': context.status,
        'message': message,
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
    # XXX this can probably provide better information about why it's forbidden
    return _error_view(context, request,
        default_message="I'm afraid I can't let you do that")

@view_config(
    context=httpexceptions.HTTPNotFound,
    renderer='error.mako')
def error404(context, request):
    # XXX this can probably be improved
    return _error_view(context, request,
        default_message=u"No such number // no such zone  ♪")
