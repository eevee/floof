import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort

from floof.lib.base import BaseController, render
from floof.lib.decorators import user_action
from floof.lib.gallery import GalleryView
from floof.lib.helpers import redirect
from floof.model import meta
from floof import model

log = logging.getLogger(__name__)

class UsersController(BaseController):

    @user_action
    def view(self, user):
        c.user_artwork_types = model.user_artwork_types
        c.related_art = {}
        for rel in model.user_artwork_types:
            c.related_art[rel] = GalleryView()
            c.related_art[rel].filter_by_user(rel, user)

        return render('/users/view.mako')

    @user_action
    def profile(self, user):
        return render('/users/profile.mako')

    @user_action
    def watchstream(self, user):
        c.artwork = GalleryView()
        c.artwork.filter_by_watches(user)

        return render('/users/watchstream.mako')
