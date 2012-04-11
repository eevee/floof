# encoding: utf8
import re
import logging
from datetime import datetime

from pyramid.view import view_config
from pyramid.view import notfound_view_config
from pyramid import httpexceptions

from floof.lib.gallery import GallerySieve
from floof.lib.pager import DiscretePager
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

    return dict(head={'status_int':httpstatuscode, 'status_msg':httpstatusmsg}, response=responsedict)


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

    comment_timedate = time(request, comment.posted_time)
    return dict(id=comment.id,
                author=comment.author.name,
                author_display=comment.author.display_name,
                content=comment.content,
                timedate=comment_timedate)


def artwork_dict(request, artwork):
    """Pass in an artwork object and this generates a standard artwork dictionary for it

    ``request``:
        Request the comment is being generated for; passed to time() function for comment timedate string

    ``artwork``:
        Artwork object used to create dictionary
    """
    rating = artwork.rating_score
    upload_timedate = time(request, artwork.uploaded_time)
    artists = artwork.user_artwork
    artist_list = []

    for user_artwork in artists:
        artist_list.append(dict(name=user_artwork.user.name, name_display=user_artwork.user.display_name))

    return dict(id=artwork.id,
                title=artwork.resource_title,
                uploader=artwork.uploader.name,
                uploader_display=artwork.uploader.display_name,
                artists=artist_list,
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


def user_dict(request, target_user):
    """Used for watchstream

    ``request``:
        Request the comment is being generated for; passed to time() function for comment timedate string

    ``target_user``:
        Target user to fetch watchstream for
    """
    activity = model.session.query(model.UserArtwork).with_parent(target_user).join(model.UserArtwork.artwork).order_by(model.Artwork.uploaded_time.desc()).limit(20)
    artwork_list = []

    for action in activity:
        artwork_list.append(action.artwork.title)

    return dict(name=target_user.name,
                name_display=target_user.display_name,
                artwork=artwork_list)
                

# -------- API.ART.BROWSE --------

@view_config(route_name='api.art.browse', renderer='json')
def api_art_browse(request):
    # Pagenum will be used, depending on what the other devs want, to call
    # the other pages generated from the art.browse route. No GET variable required.
    pagenum = 0
    artworks_list = []
    gallery_sieve = GallerySieve(user=request.user, formdata=request.GET)
    pager = gallery_sieve.evaluate()
    pager = DiscretePager(gallery_sieve.query, 64, pager.formdata_for(pagenum * 64))
    artworks = pager.items

    for artwork in pager.items:
        artworks_list.append(dict(id=artwork.id,
                                    title=artwork.title,
                                    uploader=artwork.uploader.name,
                                    uploader_display=artwork.uploader.display_name))

    return api_json_response(request, dict(artworks=artworks_list, count=pager.visible_count))

# -------- API.ART.VIEW --------

@notfound_view_config(route_name='api.art.view', renderer='json')
def api_art_view_notfound(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.art.view', renderer='json')
def api_art_view(artwork, request):
    return api_json_response(request, artwork_dict(request, artwork))

# -------- API.USERS.VIEW --------

@notfound_view_config(route_name='api.users.view', renderer='json')
def api_users_view_notfound(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.users.view', renderer='json')
def api_users_view(target_user, request):
    return api_json_response(request, user_dict(request, target_user))

# -------- API.USERS.WATCHSTREAM --------

@notfound_view_config(route_name='api.users.watchstream', renderer='json')
def api_users_watchstream(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.users.watchstream', renderer='json')
def api_users_watchstream(target_user, request):
    watched_artwork_list = []
    watches_sieve = GallerySieve(user=request.user)
    watches_sieve.filter_by_watches(target_user)
    watches_artworks = watches_sieve.query.all()

    for artwork in watches_artworks:
        watched_artwork_list.append(dict(id=artwork.id, title=artwork.title))
    
    return api_json_response(request, dict(artworks=watched_artwork_list, count=watches_sieve.query.count()))

# -------- API.TAGS.LIST --------

@view_config(route_name='api.tags.list', renderer='json')
def api_tags_list(request):
    tags = model.session.query(model.Tag).order_by(model.Tag.name)
    tags = tags_list(tags)

    return api_json_response(request, dict(tags=tags, count=tags.count()))

# -------- API.TAGS.VIEW --------

@notfound_view_config(route_name='api.tags.view', renderer='json')
def api_tags_view(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.tags.view', renderer='json')
def api_tags_view(tag, request):
    tag_artworks = model.session.query(model.Artwork).filter(model.Artwork.tag_objs.any(id=tag.id))

    return api_json_response(request, dict(count=tag_artworks.count()))

# -------- API.TAGS.ARTWORK --------

@notfound_view_config(route_name='api.tags.artwork', renderer='json')
def api_tags_artwork(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.tags.artwork', renderer='json')
def api_tags_artwork(tag, request):
    tag_artworks = model.session.query(model.Artwork).filter(model.Artwork.tag_objs.any(id=tag.id))
    artworks_list = []

    for artwork in tag_artworks:
        artworks_list.append(dict(id=artwork.id, title=artwork.title, uploader=artwork.uploader.name, uploader_display=artwork.uploader.display_name))

    return api_json_response(request, dict(artworks=artworks_list, count=tag_artworks.count()))

# -------- API.COMMENTS.LIST --------

# TODO Comments
# XXX This is a land of fuckery that I do not wish to enter
# People are going to have to know directory traversal techniques for this object to work out
# Replies of replies of replies

@notfound_view_config(route_name='api.comments.list', renderer='json')
def api_comments_list_notfound(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.comments.list', renderer='json')
def api_comments_list(discussion, request):
    set_response_notfound(request)
    return api_json_response(request, None)

# -------- API.COMMENTS.VIEW --------

@notfound_view_config(route_name='api.comments.view', renderer='json')
def api_comments_view_notfound(request):
    set_response_notfound(request)
    return api_json_response(request, None)

@view_config(route_name='api.comments.view', renderer='json')
def api_comments_view(comment, request):
    set_response_notfound(request)
    return api_json_response(request, None)
