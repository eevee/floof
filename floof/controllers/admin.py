import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from sqlalchemy.orm import subqueryload

from floof.lib.base import BaseController, render
from floof.lib.decorators import user_must
from floof.model import meta
from floof import model

log = logging.getLogger(__name__)

class AdminController(BaseController):

    @user_must('admin.view')
    def dashboard(self):
        c.current_action = 'dashboard'
        return render('/admin/dashboard.mako')

    @user_must('admin.view')
    def log(self):
        c.current_action = 'log'
        c.records = meta.Session.query(model.Log) \
            .options(subqueryload('privileges')) \
            .offset(0) \
            .limit(50)
        return render('/admin/log.mako')
