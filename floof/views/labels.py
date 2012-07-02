# encoding: utf8
import logging

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from floof import model
from floof.lib.gallery import GallerySieve

log = logging.getLogger(__name__)


@view_config(
    route_name='labels.user_index',
    renderer='labels/per_user.mako')
def index_per_user(user, request):
    """Show this user's labels."""

    return dict(
        target_user=user,
    )


@view_config(
    route_name='labels.artwork',
    request_method='GET',
    permission='label.view',
    renderer='labels/artwork.mako')
def artwork(label, request):
    """Show a gallery of artwork for this label."""
    gallery_sieve = GallerySieve(user=request.user, formdata=request.params)
    gallery_sieve.filter_by_label(label)

    return dict(
        label=label,
        gallery_sieve=gallery_sieve,
    )


@view_config(
    route_name='labels.user_index',
    request_method='POST')
def create(user, request):
    """Create a new label for this user."""
    # TODO validate the name in some manner?
    # TODO also validate the permission ahem
    album = model.Label(
        name=request.POST['name'],
        encapsulation=request.POST['privacy'],
    )
    user.labels.append(album)
    model.session.flush()

    return HTTPSeeOther(location=request.route_url('labels.user_index', user=user))
