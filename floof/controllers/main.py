import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

from floof.lib.base import BaseController, render
from floof import model
from floof.model import meta, Log

log = logging.getLogger(__name__)

class MainController(BaseController):

    def index(self):
        return render('/index.mako')

    def log(self):
        c.records = model.get_public_log_records()
        return render('/log.mako')
