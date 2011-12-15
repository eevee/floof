# encoding: utf8
import logging

from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import view_config

from floof import model
from floof.lib.gallery import GallerySieve

log = logging.getLogger(__name__)

@view_config(
    route_name='labels.user_index',
    request_method='GET',
    renderer='labels/per_user.mako')
def index_per_user(user, request):
    """Show this user's labels."""

    return dict(
        target_user=user,
    )


@view_config(
    route_name='labels.artwork',
    request_method='GET',
    renderer='labels/artwork.mako')
def artwork(label, request):
    """Show a gallery of artwork for this label."""
    # XXX this would be a good use for pyramid's authz stuff
    if label not in label.user.labels_visible_to(request.user):
        raise HTTPForbidden

    gallery_sieve = GallerySieve(user=request.user, formdata=request.params)
    gallery_sieve.filter_by_label(label)

    return dict(
        label=label,
        gallery_sieve=gallery_sieve,
    )
