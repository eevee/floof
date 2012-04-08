# encoding: utf8
import re
import logging

from pyramid.view import view_config
from pyramid import httpexceptions 

from floof.lib.gallery import GallerySieve
from floof import model

log = logging.getLogger(__name__)

"""
@view_config(
        route_name='api.test',
        request_method='GET',
        renderer='json')
def apiview(artwork, request):
    return dict(testout=request.matchdict)

@view_config(
        route_name='api',
        context=httpexceptions.HTTPNotFound,
        renderer='json')
def apierror(context, request):
    return dict(testout='This should fucking work.')
"""

def api_json_response(request, responsedict):
    """Extremely simple function that returns a standardized API JSON response

    ``request``:
        The request this is to be sent for
    ``responsedict``:
        The data you wish to display in a dictionary

    Standard response format:
        head: Contains status code and affiliated message
        content: Contains response content
    """

    httpstatusmsg = request.response.status
    httpstatuscode = request.response.status_int
    httpstatusmsg = re.sub(r'\d+\s*', "", httpstatusmsg) # Make sure the message is only a message

    return dict(head={'status':httpstatuscode, 'statusmsg':httpstatusmsg}, content=responsedict)

# API Art Stuff

@view_config(route_name='api.art.browse', renderer='json')
def api_art_browse(request):
    gallery_sieve = GallerySieve(countable=True).evaluate()
    returndict = {}
    returndict["0"] = gallery_sieve.visible_count
    count = 1 
    for a in gallery_sieve:
        returndict[int(a.id)] = {'title':a.title}
        count+=1
    return api_json_response(request.response.status_int, request.response.status, returndict)

@view_config(route_name='api.art.browse.page', renderer='json')
def api_art_browse_page(request):
    return api_json_response(request, dict(itworks=True))

@view_config(route_name='api.art.view', renderer='json')
def api_art_view(request):
    return api_json_response(request, dict(itworks=True))

# API Users Stuff

@view_config(route_name='api.users.view', renderer='json')
def api_users_view(request):
    return api_json_response(request, dict(itworks=True))

@view_config(route_name='api.users.user_index', renderer='json')
def api_users_index(request):
    return api_json_response(request, dict(itworks=True))

@view_config(route_name='api.users.watchstream', renderer='json')
def api_users_watchstream(request):
    return api_json_response(request, dict(itworks=True))

# API Tags Stuff

@view_config(route_name='api.tags.list', renderer='json')
def api_tags_list(request):
    return api_json_response(request, dict(itworks=True))

@view_config(route_name='api.tags.view', renderer='json')
def api_tags_view(request):
    return api_json_response(request, dict(itworks=True))

@view_config(route_name='api.tags.artwork', renderer='json')
def api_tags_artwork(request):
    return api_json_response(request, dict(itworks=True))
