# encoding: utf8
import logging

from pyramid import httpexceptions
from pyramid.response import Response
from pyramid.view import view_config

log = logging.getLogger(__name__)

@view_config(route_name='debug.blank')
def blank(context, request):
    return Response(body='')


@view_config(route_name='debug.status.303')
def raise_303(context, request):
    raise httpexceptions.HTTPSeeOther(location=request.route_url('debug.blank'))

@view_config(route_name='debug.status.400')
def raise_400(context, request):
    raise httpexceptions.HTTPBadRequest()

@view_config(route_name='debug.status.403')
def raise_403(context, request):
    raise httpexceptions.HTTPForbidden()

@view_config(route_name='debug.status.404')
def raise_404(context, request):
    raise httpexceptions.HTTPNotFound()


@view_config(route_name='debug.crash')
def crash(context, request):
    raise Exception()

@view_config(route_name='debug.mako-crash', renderer='crash.mako')
def mako_crash(context, request):
    return {}
