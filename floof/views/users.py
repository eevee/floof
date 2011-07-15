# encoding: utf8
import logging

from pyramid.view import view_config

from floof.lib.gallery import GallerySieve
from floof import model

log = logging.getLogger(__name__)

@view_config(
    route_name='users.view',
    request_method='GET',
    renderer='users/view.mako')
def view(target_user, request):
    related_art = {}
    for rel in model.user_artwork_types:
        related_art[rel] = GallerySieve(user=request.user)
        related_art[rel].filter_by_user(rel, target_user)

    return dict(
        target_user=target_user,
        user_artwork_types=model.user_artwork_types,
        related_art=related_art,
    )


@view_config(
    route_name='users.profile',
    request_method='GET',
    renderer='users/profile.mako')
def profile(target_user, request):
    return dict(target_user=target_user)


@view_config(
    route_name='users.watchstream',
    request_method='GET',
    renderer='users/watchstream.mako')
def watchstream(target_user, request):
    artwork = GallerySieve(user=request.user)
    artwork.filter_by_watches(target_user)

    return dict(
        artwork=artwork,
        target_user=target_user,
    )


@view_config(
    route_name='users.art_by_label',
    request_method='GET',
    renderer='users/label.mako')
def art_by_label(target_user, request):
    if label not in model.user_artwork_types:
        raise NotImplementedError  # XXX

    rel = request.matchdict['label']
    gallery_sieve = GallerySieve(user=request.user, formdata=request.GET, countable=True)
    gallery_sieve.filter_by_user(rel, target_user)

    return dict(
        rel=rel,
        gallery_sieve=gallery_sieve,
    )
