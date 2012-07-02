# encoding: utf8
import logging

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from floof import model
from floof.lib.gallery import GallerySieve

log = logging.getLogger(__name__)


@view_config(
    route_name='albums.user_index',
    renderer='albums/per_user.mako')
def index_per_user(user, request):
    """Show this user's albums."""

    return dict(
        target_user=user,
    )


@view_config(
    route_name='albums.artwork',
    request_method='GET',
    permission='album.view',
    renderer='albums/artwork.mako')
def artwork(album, request):
    """Show a gallery of artwork for this album."""
    gallery_sieve = GallerySieve(user=request.user, formdata=request.params)
    gallery_sieve.filter_by_album(album)

    return dict(
        album=album,
        gallery_sieve=gallery_sieve,
    )


@view_config(
    route_name='albums.user_index',
    request_method='POST')
def create(user, request):
    """Create a new album for this user."""
    # TODO validate the name in some manner?
    # TODO also validate the permission ahem
    album = model.Album(
        name=request.POST['name'],
        encapsulation=request.POST['privacy'],
    )
    user.albums.append(album)
    model.session.flush()

    return HTTPSeeOther(location=request.route_url('albums.user_index', user=user))
