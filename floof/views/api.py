# encoding: utf8
import re
import logging
from datetime import datetime

from pyramid.view import view_config
from pyramid import httpexceptions 

from floof.lib.gallery import GallerySieve
from floof import model

log = logging.getLogger(__name__)

""" Keeping this here, worked before for overriding default HTTPNotFound page
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
        The data you wish to display as a python dictionary

    Standard response format:
        head: Contains status code and affiliated message
        content: Contains response content
    """

    httpstatusmsg = re.sub(r'\d+\s*', "", request.response.status)
    httpstatuscode = request.response.status_int

    return dict(head={'status':httpstatuscode, 'statusmsg':httpstatusmsg}, content=responsedict)

def time(request, t):
    return request.user.localtime(t).strftime('%A, %d %B %Y at %H:%M %Z')

def comment_dict(request, comment):
    authorobj = model.session.query(model.User) \
                .filter(model.User.id==comment.author_user_id) \
                .first()
    comment_timedate = time(request, comment.posted_time)
    return dict(id=comment.id,
                author=authorobj.name,
                author_display=authorobj.display_name,
                content=comment.content,
                timedate=comment_timedate)


# API Art Stuff

@view_config(route_name='api.art.browse', renderer='json')
def api_art_browse(request):
    gallery_sieve = GallerySieve(countable=True).evaluate()
    return api_json_response(request, dict(count=gallery_sieve.visible_count))

@view_config(route_name='api.art.view', renderer='json')
def api_art_view(artwork, request):
    rating = artwork.rating_score
    userobj = model.session.query(model.User) \
            .filter(model.User.id==artwork.uploader_user_id) \
            .first()
    upload_timedate = time(request, artwork.uploaded_time)
    comments = artwork.discussion.comments
    comments_list = []

    for comment in comments:
        comment_timedate = time(request, comment.posted_time)
        comments_list.append(comment_dict(request, comment))

    return api_json_response(request, dict(id=artwork.id,
                                            title=artwork.title,
                                            uploader=userobj.name,
                                            uploader_display=userobj.display_name,
                                            rating=rating,
                                            remark=artwork.remark,
                                            comments=comments_list,
                                            timedate=upload_timedate,
                                            filename=artwork.original_filename,
                                            filesize=artwork.file_size,
                                            dimensionx=artwork.width,
                                            dimensiony=artwork.height,
                                            hash=artwork.hash))


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
