import logging
import os
import subprocess

from pyramid_beaker import session_factory_from_settings
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.events import BeforeRender, ContextFound, NewRequest
from pyramid.request import Request
from pyramid.settings import asbool
from sqlalchemy import engine_from_config
import transaction
import webob.request
from zope.sqlalchemy import ZopeTransactionExtension

from floof.lib.authn import Authenticizer, FloofAuthnPolicy
from floof.lib.authz import auto_privilege_escalation
from floof.lib.authz import current_view_permission
from floof.lib.stash import manage_stashes
from floof.model import filestore
from floof.resource import FloofRoot

import floof.lib.helpers
import floof.model
import floof.routing
import floof.views

log = logging.getLogger(__name__)


# Raised when the CSRF token check fails but no cookies have been sent
class NoCookiesError(Exception): pass


def get_shim(name):
    def _dictlike_get_shim(self):
        return self.__dict__.get(name)
    return _dictlike_get_shim


class FloofRequest(Request):
    @reify
    def auth(self):
        auth = Authenticizer(self)
        self.session.changed()
        return auth

    # floof auth assumes some properties always exist, which might not
    context = property(get_shim('context'))
    root = property(get_shim('root'))

    @property
    def permission(self):
        # Not reified as this may be erroneously called before ContextFound
        return current_view_permission(self)

    @reify
    def storage(self):
        storage = self.registry.settings['filestore_factory']()
        transaction.get().join(storage)
        return storage

    @property
    def user(self):
        return self.auth.user


class _RichSessionFlashMixin(object):
    """Tack me onto a standard Pyramid session class to store the flash as
    dicts instead of strings.
    """

    _default_flash_icons = dict(
        error='exclamation-red-frame',
        warning='exclamation-diamond-frame',
        notice='hand-point',
        success='tick-circle',
    )

    def flash(self, message, icon=None, level='notice', html_escape=True, **kwargs):
        """Store your flash message with an optional icon and "level" (which
        really just affects the CSS class).
        """
        assert level in self._default_flash_icons

        if icon is None:
            icon = self._default_flash_icons[level]

        to_store = dict(message=message, icon=icon, level=level,
                        html_escape=html_escape)
        super(_RichSessionFlashMixin, self).flash(to_store, **kwargs)


class HTTPOnlyCookieMiddleware(object):
    """Middleware that catches Set-Cookie headers and forces them to be
    HTTPOnly, preventing session hijacking attacks in most browsers.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = webob.request.Request(environ)
        res = req.get_response(self.app)

        # There's also res.headers, but directly changing a value seems to be
        # tricky with a multidict.  This is kinda lame but works fine
        for i, (key, val) in enumerate(res.headerlist):
            if key.lower() == 'set-cookie' and 'httponly' not in val.lower():
                res.headerlist[i] = (key, val + '; HTTPOnly')

        return res(environ, start_response)

def add_renderer_globals(event):
    """Add any globals that should be available to Mako."""
    event['h'] = floof.lib.helpers

def prevent_csrf(event):
    """Require a CSRF token on all POST requests.

    Ignore tests, though, for dev sanity.
    """
    request = event.request
    if (request.method == 'POST' and
        'paste.testing' not in request.environ and
        not request.path.startswith('/_debug_toolbar/') and
        request.POST.get('csrf_token', None)
            != request.session.get_csrf_token()):

        # Token is wrong!
        if not request.cookies:
            raise NoCookiesError

        from pyramid.exceptions import Forbidden
        raise Forbidden('Possible cross-site request forgery detected.')


def main(global_config, **settings):
    """Constructs a WSGI application."""
    settings['paste_config'] = global_config

    ### Settings
    # Set up SQLAlchemy stuff
    engine = engine_from_config(settings, 'sqlalchemy.')
    floof.model.initialize(
        engine, extension=ZopeTransactionExtension())

    # floof debug panel
    settings['debug'] = asbool(settings.get('floof.debug', False))

    # Misc other crap
    settings['rating_radius'] = int(settings['rating_radius'])
    settings['filestore_factory'] = filestore.get_storage_factory(settings)

    ### Configuratify
    # Session factory needs to subclass our mixin above.  Beaker's
    # verbosely-named function just returns a class, so do some MI
    FloofSessionFactory = type('FloofSessionFactory',
        (_RichSessionFlashMixin,
            session_factory_from_settings(settings)),
        {})

    config = Configurator(
        settings=settings,
        root_factory=FloofRoot,
        request_factory=FloofRequest,
        session_factory=FloofSessionFactory,
        authentication_policy=FloofAuthnPolicy(),
        authorization_policy=ACLAuthorizationPolicy(),
    )

    # PySCSS support
    config.include('pyramid_scss')
    config.add_route('pyscss', '/css/{css_path:[^/]+}.css')
    config.add_view(route_name='pyscss', view='pyramid_scss.controller.get_scss', renderer='scss', request_method='GET')

    # Added manually because @subscriber only works with a
    # scan, and we don't want to scan ourselves
    config.add_subscriber(prevent_csrf, NewRequest)
    config.add_subscriber(manage_stashes, NewRequest)
    config.add_subscriber(auto_privilege_escalation, ContextFound)
    config.add_subscriber(add_renderer_globals, BeforeRender)

    floof.routing.configure_routing(config)
    config.scan(floof.views)

    if not settings['debug']:
        from floof.views.errors import error500
        config.add_view(error500, context=Exception)

    app = config.make_wsgi_app()
    app = HTTPOnlyCookieMiddleware(app)
    return app
