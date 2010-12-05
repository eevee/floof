import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from floof.lib.base import BaseController, render

log = logging.getLogger(__name__)

class ControlsController(BaseController):

    def index(self):
        return render('/account/controls/index.mako')
