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
    apiobj = APIResponse(request, return_type="xml")
    if apiobj.is_valid():
        return dict(testout="Success!")
    else:
        return dict(testout="Failure!")

class APIResponse(object):
    def __init__(self, request, return_type=''):
        self.content_type = request.content_type
        self.return_type = return_type
    def is_valid(self):
        if not '/xml' in self.content_type or not '/json' in self.content_type and return_type in self.content_type:
            return False
        else:
            return True
