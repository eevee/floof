# encoding: utf8
import logging

from pyramid.view import view_config

from pyramid import httpexceptions 

from floof.lib.gallery import GallerySieve
from floof import model

log = logging.getLogger(__name__)

# A rule of three
# The three most basic operations
#
#   1. Insert
#   2. Modify
#   3. Delete

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

@view_config(
        route_name='api.art.browse',
        renderer='json')
def apibase(request):
    gallery_sieve = GallerySieve(countable=True)
    gallery_sieve = gallery_sieve.evaluate()
    returndict = {}
    returndict['size'] = gallery_sieve.visible_count
    count = 1 
    for a in gallery_sieve:
        returndict[count] = {'id':a.id, 'title':a.title}
        count+=1

    return dict(returndict)
