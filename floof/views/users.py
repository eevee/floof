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
    # TODO flesh this out into multiple types of actions
    activity = model.session.query(model.UserArtwork).with_parent(target_user).join(model.UserArtwork.artwork).order_by(model.Artwork.uploaded_time.desc()).limit(20)

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
    route_name='users.art',
    request_method='GET',
    renderer='users/art.mako')
def art(target_user, request):
    artwork = GallerySieve(user=request.user)
    artwork.filter_by_watches(target_user)

    return dict(
        artwork=artwork,
        target_user=target_user,
    )


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
    route_name='users.art_by_album',
    request_method='GET',
    renderer='users/album.mako')
def art_by_album(target_user, request):
    if album not in model.user_artwork_types:
        raise NotImplementedError  # XXX

    rel = request.matchdict['album']
    gallery_sieve = GallerySieve(user=request.user, formdata=request.GET, countable=True)
    gallery_sieve.filter_by_user(rel, target_user)

    return dict(
        rel=rel,
        gallery_sieve=gallery_sieve,
    )


@view_config(
    route_name='api:users.list',
    renderer='json',
)
def api_user_list(request):
    q = model.session.query(model.User)

    if request.GET.get('name'):
        # TODO escape LIKE syntax, and maybe also search display name
        q = q.filter(model.User.name.like('%' + request.GET['name'] + '%'))

    users = q.all()

    # TODO need a more better way to define the api repr of an orm object
    data = []
    for user in users:
        data.append(dict(
            id=user.id,
            name=user.name,
        ))

    # TODO and a wrapper for this kind of common thing
    return {
        'status': 'success',
        'results': data,
    }
