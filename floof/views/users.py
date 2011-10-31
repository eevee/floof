# encoding: utf8
import logging

from pyramid.view import view_config

from floof.lib.gallery import GallerySieve
from floof import model
from floof.model import meta

log = logging.getLogger(__name__)

@view_config(
    route_name='users.view',
    request_method='GET',
    renderer='users/view.mako')
def view(target_user, request):
    # TODO flesh this out into multiple types of actions
    activity = meta.Session.query(model.UserArtwork).with_parent(target_user).join(model.UserArtwork.artwork).order_by(model.Artwork.uploaded_time.desc()).limit(20)

    return dict(
        target_user=target_user,
        activity=activity,
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
