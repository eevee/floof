# encoding: utf8
import logging

from pyramid.view import view_config

from floof import model

log = logging.getLogger(__name__)

@view_config(
    route_name='admin.dashboard',
    permission='admin.view',
    request_method='GET',
    renderer='admin/dashboard.mako')
def dashboard(context, request):
    return dict(current_action='dashboard')

@view_config(
    route_name='admin.log',
    permission='admin.view',
    request_method='GET',
    renderer='admin/log.mako')
def log_(context, request):
    records = model.session.query(model.Log) \
        .offset(0) \
        .limit(50)
    return dict(
        current_action='log',
        records=records,
    )
