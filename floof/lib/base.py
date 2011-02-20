"""The base Controller API

Provides the BaseController class for subclassing.
"""
import datetime

from pylons import config, request, session, tmpl_context as c
from pylons.controllers import WSGIController
from pylons.controllers.util import abort
from pylons.templating import render_mako
from pylons.decorators.secure import authenticated_form
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
import webhelpers.pylonslib.secure_form as secure_form
import wtforms.fields, wtforms.form

from floof.lib import auth
from floof.lib.debugging import ResponseTimer
from floof.lib.helpers import flash
from floof.model import AnonymousUser, User, meta
from floof import model

def render(*args, **kwargs):
    if config['super_debug']:
        start_time = datetime.datetime.now()
        sql_start_time = c.timer.sql_time

    ret = render_mako(*args, **kwargs)

    if config['super_debug']:
        c.timer.template_time += (datetime.datetime.now()
            - start_time
            - (c.timer.sql_time - sql_start_time)
        )

    return ret

class BaseController(WSGIController):
    class CommentForm(wtforms.form.Form):
        message = wtforms.fields.TextAreaField(label=u'')


    def __before__(self, action, environ, **params):
        c.timer = ResponseTimer()
        
        c.auth = auth.Auth(session, environ)
        c.user = c.auth.get_user()

        # Check CSRF token on POST requests.  Ignore during test runs
        if request.method == 'POST' and not 'paste.testing' in environ:
            if not authenticated_form(request.POST):
                abort(400, detail='Possible cross-site request forgery detected.')


    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            if not 'paste.testing' in environ:
                # Tests take care of the session removal on their own;
                # otherwise object identity isn't the same between app and test
                meta.Session.remove()
