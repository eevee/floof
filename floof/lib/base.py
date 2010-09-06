"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons import session, tmpl_context as c
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from sqlalchemy.orm.exc import NoResultFound

from floof.model import AnonymousUser, User, meta

class BaseController(WSGIController):

    def __before__(self, action, environ, **params):
        # Check user state
        if 'tests.user_id' in environ:
            user_id = environ['tests.user_id']
        elif 'user_id' in session:
            user_id = session['user_id']

        try:
            c.user = meta.Session.query(User).filter_by(id=user_id).one()
        except (NameError, NoResultFound):
            c.user = AnonymousUser()

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()
