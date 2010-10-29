import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

from floof.lib.base import BaseController, render
from floof.lib.decorators import user_action
from floof.model import meta
from floof import model

log = logging.getLogger(__name__)

class UsersController(BaseController):

    @user_action
    def view(self, user):
        c.related_art = {}
        for rel in meta.Session.query(model.UserArtwork).filter_by(user=user):
            c.related_art.setdefault(rel.relationship_type, []).append(rel.artwork)
        return render('/users/view.mako')

    @user_action
    def profile(self, user):
        return render('/users/profile.mako')
