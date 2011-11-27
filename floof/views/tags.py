# encoding: utf8
import logging

from pyramid.view import view_config

from floof import model
from floof.lib.gallery import GallerySieve

log = logging.getLogger(__name__)

@view_config(
    route_name='tags.list',
    request_method='GET',
    renderer='tags/index.mako')
def index(context, request):
    q = model.session.query(model.Tag).order_by(model.Tag.name)
    return dict(
        tags=q,
    )


@view_config(
    route_name='tags.view',
    request_method='GET',
    renderer='tags/view.mako')
def view(tag, request):
    return dict(tag=tag)


@view_config(
    route_name='tags.artwork',
    request_method='GET',
    renderer='tags/artwork.mako')
def artwork(tag, request):
    """Show a gallery of artwork for this tag."""
    gallery_sieve = GallerySieve(user=request.user, formdata=request.params)
    gallery_sieve.filter_by_tag(tag.name)  # XXX this seems inefficient.

    return dict(
        tag=tag,
        gallery_sieve=gallery_sieve,
    )
