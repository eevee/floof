import functools
import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

from floof.lib.base import BaseController, render
from floof.model import meta
from floof import model

log = logging.getLogger(__name__)

def user_action(f):
    @functools.wraps(f)
    def wrap(self, id=None, name=None):
        q = meta.Session.query(model.User)
        if name is not None:
            user = q.filter_by(name=name).first()
        else:
            user = q.get(id)
        if user is None:
            abort(404)
        c.this_user = user
        return f(self, user)
    return wrap

class UserController(BaseController):

    @user_action
    def view(self, user):
        return render('/user/view.mako')

    @user_action
    def profile(self, user):
        return render('/user/profile.mako')
