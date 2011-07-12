# encoding: utf8
import logging

from pyramid.exceptions import Forbidden, NotFound
from pyramid.view import view_config

log = logging.getLogger(__name__)

@view_config(
    context=Forbidden,
    renderer='error.mako')
@view_config(
    context=NotFound,
    renderer='error.mako')
def error(context, request):
    return dict(
        status=context.status,
        message=context.args[0],
    )
