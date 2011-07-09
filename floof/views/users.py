# encoding: utf8
import logging

from pyramid.view import view_config

from floof.lib.gallery import GallerySieve
from floof import model

log = logging.getLogger(__name__)

# XXX @user_action
@view_config(
    route_name='users.view',
    request_method='GET',
    renderer='users/view.mako')
def view(context, request):
    target_user = request.user  # XXX
    related_art = {}
    for rel in model.user_artwork_types:
        related_art[rel] = GallerySieve(user=request.user)
        related_art[rel].filter_by_user(rel, target_user)

    return dict(
        target_user=target_user,
        user_artwork_types=model.user_artwork_types,
        related_art=related_art,
    )

# XXX @user_action
@view_config(
    route_name='users.profile',
    request_method='GET',
    renderer='users/profile.mako')
def profile(context, request):
    target_user = request.user  # XXX
    return dict(target_user=target_user)

# XXX @user_action
@view_config(
    route_name='users.watchstream',
    request_method='GET',
    renderer='users/watchstream.mako')
def watchstream(context, request):
    target_user = request.user  # XXX
    artwork = GallerySieve(user=request.user)
    artwork.filter_by_watches(target_user)

    return dict(
        artwork=artwork,
        target_user=target_user,
    )

# XXX @user_action
@view_config(
    route_name='users.art_by_label',
    request_method='GET',
    renderer='users/label.mako')
def art_by_label(context, request):
    if label not in model.user_artwork_types:
        raise NotImplementedError  # XXX

    target_user = request.user  # XXX
    rel = request.matchdict['label']
    gallery_sieve = GallerySieve(user=request.user, formdata=request.GET, countable=True)
    gallery_sieve.filter_by_user(rel, target_user)

    return dict(
        rel=rel,
        gallery_sieve=gallery_sieve,
    )
