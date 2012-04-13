# encoding: utf8
import logging

from pyramid.view import view_config, view_defaults
from pyramid.view import notfound_view_config
from pyramid import httpexceptions

from floof.lib.gallery import GallerySieve
from floof.lib.pager import DiscretePager
from floof import model

log = logging.getLogger(__name__)


def tags_list(artwork):
    """Input Artwork object, output normal PythonList from InstrumentedList of Artwork.tag_objs

    ``artwork``:
        Artwork object that the function uses to get the tag_objs list
    """

    return_list = []
    for tag in artwork.tag_objs:
        return_list.append(tag.name)
    return return_list


def comment_dict(comment):
    """Pass in a comment object and this generates a standard comment dictionary for it

    Best use-case: generating comment list

    ``comment``:
        Comment object used to create the dictionary
    """

    return dict(id=comment.id,
                author=comment.author.name,
                author_display=comment.author.display_name,
                content=comment.content,
                timedate=comment.posted_time.isoformat())


def artwork_dict(artwork, request):
    """Pass in an artwork object and this generates a standard artwork dictionary for it

    ``artwork``:
        Artwork object used to create dictionary
    ``request``:
        The request this is to be sent for; used to generate URLs
    """
    rating = artwork.rating_score
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
                timedate=artwork.uploaded_time.isoformat(),
                filename=artwork.filename,
                filename_old=artwork.original_filename,
                filesize=artwork.file_size,
                dimension_x=artwork.width,
                dimension_y=artwork.height,
                hash=artwork.hash,
                url=request.route_url('filestore', class_=u'artwork', key=artwork.hash))


def user_dict(request, target_user):
    """Used for watchstream

    ``target_user``:
        Target user to fetch watchstream for
    """
    activity = model.session.query(model.UserArtwork).with_parent(target_user).join(model.UserArtwork.artwork).order_by(model.Artwork.uploaded_time.desc()).limit(20)
    artwork_list = []

    for action in activity:
        artwork_list.append(action.artwork.resource_title)

    return dict(name=target_user.name,
                name_display=target_user.display_name,
                artwork=artwork_list)


@view_defaults(renderer='json')
class API(object):
    def __init__(self, request):
        self.request = request
        self.context = request.context

    # XXX: Perhaps there is a nicer/more automatic way of doing this?
    # Note that class view defaults do not appear to apply to
    # notfound_view_config
    notfound = lambda r: notfound_view_config(route_name=r,
                                              renderer='json')
    @notfound('api.art.view')
    @notfound('api.users.view')
    @notfound('api.users.watchstream')
    @notfound('api.tags.view')
    @notfound('api.tags.artwork')
    @notfound('api.comments.list')
    @notfound('api.comments.view')
    def api_notfound(self):
        self.request.response.status = 404
        return None

    # -------- API.ART.BROWSE --------

    @view_config(route_name='api.art.browse')
    def api_art_browse(self):
        # Pagenum will be used, depending on what the other devs want, to call
        # the other pages generated from the art.browse route. No GET variable required.
        pagenum = 0
        artworks_list = []
        gallery_sieve = GallerySieve(user=self.request.user, formdata=self.request.GET)
        pager = gallery_sieve.evaluate()
        pager = DiscretePager(gallery_sieve.query, 64, pager.formdata_for(pagenum * 64))

        for artwork in pager.items:
            artworks_list.append(dict(id=artwork.id,
                                        title=artwork.resource_title,
                                        uploader=artwork.uploader.name,
                                        uploader_display=artwork.uploader.display_name))

        return dict(artworks=artworks_list, count=pager.visible_count)

    # -------- API.ART.VIEW --------

    @view_config(route_name='api.art.view')
    def api_art_view(self):
        artwork = self.context
        return artwork_dict(artwork, self.request)

    # -------- API.USERS.VIEW --------


    @view_config(route_name='api.users.view')
    def api_users_view(self):
        target_user = self.context
        return user_dict(self.request, target_user)

    # -------- API.USERS.WATCHSTREAM --------

    @view_config(route_name='api.users.watchstream')
    def api_users_watchstream(self):
        target_user = self.context
        watched_artwork_list = []
        watches_sieve = GallerySieve(user=self.request.user)
        watches_sieve.filter_by_watches(target_user)
        watches_artworks = watches_sieve.query.all()

        for artwork in watches_artworks:
            watched_artwork_list.append(dict(id=artwork.id, title=artwork.resource_title))

        return dict(
            artworks=watched_artwork_list,
            count=watches_sieve.query.count()
        )

    # -------- API.TAGS.LIST --------

    @view_config(route_name='api.tags.list')
    def api_tags_list(self):
        tags = model.session.query(model.Tag).order_by(model.Tag.name)
        count = tags.count()
        tags = [t.name for t in tags.all()]

        return dict(tags=tags, count=count)

    # -------- API.TAGS.VIEW --------

    @view_config(route_name='api.tags.view')
    def api_tags_view(self):
        tag = self.context
        tag_artworks = model.session.query(model.Artwork).filter(model.Artwork.tag_objs.any(id=tag.id))

        return dict(count=tag_artworks.count())

    # -------- API.TAGS.ARTWORK --------

    @view_config(route_name='api.tags.artwork')
    def api_tags_artwork(self):
        tag = self.context
        tag_artworks = model.session.query(model.Artwork).filter(model.Artwork.tag_objs.any(id=tag.id))
        artworks_list = []

        for artwork in tag_artworks:
            artworks_list.append(dict(id=artwork.id, title=artwork.resource_title, uploader=artwork.uploader.name, uploader_display=artwork.uploader.display_name))

        return dict(artworks=artworks_list, count=tag_artworks.count())

    # -------- API.COMMENTS.LIST --------

    # TODO Comments
    # XXX This is a land of fuckery that I do not wish to enter
    # People are going to have to know directory traversal techniques for this object to work out
    # Replies of replies of replies

    @view_config(route_name='api.comments.list')
    def api_comments_list(self):
        self.request.response.status = 404
        return None

    # -------- API.COMMENTS.VIEW --------

    @view_config(route_name='api.comments.view')
    def api_comments_view(self):
        self.request.response.status = 404
        return None
