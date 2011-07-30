# encoding: utf8
import logging

from pyramid import httpexceptions
from pyramid.view import view_config

log = logging.getLogger(__name__)

@view_config(route_name='debug.status.400')
def raise_400(context, request):
    raise httpexceptions.HTTPBadRequest()

@view_config(route_name='debug.status.403')
def raise_403(context, request):
    raise httpexceptions.HTTPForbidden()

@view_config(route_name='debug.status.404')
def raise_404(context, request):
    raise httpexceptions.HTTPNotFound()
