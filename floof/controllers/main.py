import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort

from floof.lib.base import BaseController, render
from floof.lib.helpers import redirect
from floof.lib.log import ADMIN
from floof import model
from floof.model import meta, Log

log = logging.getLogger(__name__)

class MainController(BaseController):

    def index(self):
        return render('/index.mako')

    def cookies_disabled(self):
        if request.cookies:
            # Something odd has happened, but the "you've got cookies
            # disabled" message is clearly inappropriate here.
            redirect(url(controller='account', action='login'))
        return render('/cookies_disabled.mako')

    def log(self):
        c.records = meta.Session.query(model.Log) \
            .filter_by(level=ADMIN) \
            .offset(0) \
            .limit(50)
        return render('/log.mako')
