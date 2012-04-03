# encoding: utf8
import logging

from pyramid.view import view_config

from floof import model

log = logging.getLogger(__name__)

# TODO Now, the fun: return format determined by file extension or accepted headers
# Methods executed by extraneous URIs "/api/delete/:id" or by request method GET, DELETE, etc.
@view_config(
        route_name='api.test',
        request_method='GET',
        renderer='api.test.mako')
def apiview(request):
    return dict(testout="Success.")
