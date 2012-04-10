# encoding: utf8
import re
import logging
from datetime import datetime

from pyramid.view import view_config
from pyramid.view import notfound_view_config
from pyramid import httpexceptions

from floof.lib.gallery import GallerySieve
from floof import model

log = logging.getLogger(__name__)


def api_json_response(request, responsedict):
    """Extremely simple function that returns a standardized API JSON response

    HEADS UP: To have your responsedict rendered as empty, every key`s value must be None or responsedict must be None.

    ``request``:
        The request this is to be sent for
    ``responsedict``:
        The data you wish to display as a python dictionary

    Standard response format:
        head: Contains status code and affiliated message
        body: Contains response content
    """

    httpstatusmsg = re.sub(r'\A\d+\s*', "", request.response.status)
    httpstatuscode = request.response.status_int

    # If the responsedict is empty, body should be empty.
    if responsedict:
        empty_flag = True

        for kvpair in responsedict.items():
            if kvpair[1] is not None:
                empty_flag = False

        if empty_flag:
            responsedict = None

    return dict(head={'status_int':httpstatuscode, 'status_msg':httpstatusmsg}, body=responsedict)


def time(request, t):
    """Return time string for given datetime `t`; this is the same function that`s used on the template pages

    ``request``:
        Request time is being gathered for

    ``t``:
        Datetime to create string for
    """

    return request.user.localtime(t).strftime('%A, %d %B %Y at %H:%M %Z')


def set_response_notfound(request):
    """Pass in a request and this small utility changes its status code and message to `404 Not Found`

    ``request``:
        The request you need to change the status headers for.
    """

    request.response.status = u'404 Not Found'
    request.response.status_int = 404
    return request


def tags_list(artwork):
    """Input Artwork object, output normal PythonList from InstrumentedList of Artwork.tag_objs

    ``artwork``:
        Artwork object that the function uses to get the tag_objs list
    """

    return_list = []
    for tag in artwork.tag_objs:
        return_list.append(tag.name)
    return return_list


def comment_dict(request, comment):
    """Pass in a comment object and this generates a standard comment dictionary for it

    Best use-case: generating comment list

    ``request``:
        Request the comment is being generated for; passed to time() function for comment timedate string

    ``comment``:
        Comment object used to create the dictionary
    """

    authorobj = model.session.query(model.User) \
                .filter(model.User.id==comment.author_user_id) \
                .first()
    comment_timedate = time(request, comment.posted_time)
    return dict(id=comment.id,
                author=authorobj.name,
                author_display=authorobj.display_name,
                content=comment.content,
                timedate=comment_timedate)


def artwork_dict(request, artwork):
    rating = artwork.rating_score
    userobj = model.session.query(model.User) \
            .filter(model.User.id==artwork.uploader_user_id) \
            .first()
    upload_timedate = time(request, artwork.uploaded_time)

    return dict(id=artwork.id,
                title=artwork.resource_title,
                uploader=userobj.name,
                uploader_display=userobj.display_name,
                rating=rating or 0,
                tags=tags_list(artwork) or None,
                remark=artwork.remark or None,
                timedate=upload_timedate,
                filename=artwork.filename,
                filename_old=artwork.original_filename,
                filesize=artwork.file_size,
                dimension_x=artwork.width,
                dimension_y=artwork.height,
                hash=artwork.hash,
                url=request.route_url('filestore', class_=u'artwork', key=artwork.hash))



# -------- API.ART.BROWSE --------

@view_config(route_name='api.art.browse', renderer='json')
def api_art_browse(request):
    gallery_sieve = GallerySieve(countable=True).evaluate()
    count = gallery_sieve.visible_count or None

    return api_json_response(request, dict(count=count))

# -------- API.ART.VIEW --------

@view_config(route_name='api.art.view', context=httpexceptions.HTTPNotFound, renderer='json')
def api_art_view_notfound(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.art.view', renderer='json')
def api_art_view(artwork, request):
    return api_json_response(request, artwork_dict(request, artwork))

# -------- API.USERS.VIEW --------

@view_config(route_name='api.users.view', renderer='json')
def api_users_view(request):
    return api_json_response(request, dict(itworks=True))

# -------- API.USERS.USER_INDEX --------

@view_config(route_name='api.users.user_index', renderer='json')
def api_users_index(request):
    return api_json_response(request, dict(itworks=True))

# -------- API.USERS.WATCHSTREAM --------

@view_config(route_name='api.users.watchstream', renderer='json')
def api_users_watchstream(request):
    return api_json_response(request, dict(itworks=True))


# -------- API.TAGS.LIST --------

@view_config(route_name='api.tags.list', renderer='json')
def api_tags_list(request):
    return api_json_response(request, dict(itworks=True))

# -------- API.TAGS.VIEW --------

@view_config(route_name='api.tags.view', renderer='json')
def api_tags_view(request):
    return api_json_response(request, dict(itworks=True))

# -------- API.TAGS.ARTWORK --------

@view_config(route_name='api.tags.artwork', renderer='json')
def api_tags_artwork(request):
    return api_json_response(request, dict(itworks=True))


# -------- API.COMMENTS.LIST --------

@view_config('api.comments.list', renderer='json')
def api_comments_list(request):
    pass

# -------- API.COMMENTS.VIEW --------

@view_config('api.comments.view', renderer='json')
def api_comments_view(request):
    pass
