from datetime import timedelta
import logging
import os
import subprocess

from pyramid_beaker import session_factory_from_settings
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.events import BeforeRender, ContextFound, NewRequest, NewResponse
from pyramid.request import Request
from pyramid.security import has_permission
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

import floof.lib.debugging
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
    def __init__(self, *args, **kwargs):
        self.timer = floof.lib.debugging.RequestTimer()
        super(FloofRequest, self).__init__(*args, **kwargs)

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

def start_template_timer(event):
    """Inform the request's timer object to switch to recording rendering time.
    """
    event['request'].timer.switch_timer('mako')

def flush_everything(event):
    # XXX this is a hack to make the timer stuff not explode.  repoze.tm
    # commits after the request has already gone away, which breaks it.  try
    # flushing first so the commit doesn't trigger the sqla listeners.  :/
    floof.model.session.flush()

def log_timers(event):
    """Log the state of the timers; for production when super_debug is off.
    """
    if not event.request.registry.settings.get('super_debug', False):
        total_time = event.request.timer.total_time  # NB: this stops all timing

        # Don't log if Mako doesn't appear to have been invoked, thus avoiding
        # the logging of requests for static content
        # TODO: Work out if this is too hackish as a criterion
        if event.request.timer.timers.get('mako', timedelta(0)) <= timedelta(0):
            return

        t = []
        for name, delta in event.request.timer.timers.iteritems():
            t.append('{0}: {1}.{2:0>6}s'.format(
                    name, delta.seconds, delta.microseconds))

        log.debug('Request process times: TOTAL: {0}.{1:0>6}s, {2}'.format(
            total_time.seconds, total_time.microseconds, ', '.join(t)))

def prevent_csrf(event):
    """Require a CSRF token on all POST requests.

    Ignore tests, though, for dev sanity.
    """
    request = event.request
    if (request.method == 'POST' and
        'paste.testing' not in request.environ and
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

    # Compile stylesheets with Sass
    # This env var is only set from a convenient dev-mode launcher script
    # XXX uh this could just be in the .ini
    if 'FLOOF_SKIP_SASS_COMPILATION' not in os.environ:
        # XXX consult pyramid for the location?
        compile_sass(global_config['here'] + '/floof')

    ### Settings
    # Set up SQLAlchemy stuff
    engine = engine_from_config(settings, 'sqlalchemy.')
    floof.model.initialize(
        engine, extension=ZopeTransactionExtension())

    # floof debug panel
    settings['super_debug'] = asbool(settings.get('super_debug', False))
    # Listeners to record query time, et al.
    # XXX disable this normally; nobody cares about these stats but devs.  just
    # show the stats to devs and make the debug thing optional.  (can these
    # listeners even be enabled per-request?  if not, should we log the stats?)
    floof.lib.debugging.attach_sqlalchemy_listeners(engine, settings['super_debug'])

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

    # Added manually because @subscriber only works with a
    # scan, and we don't want to scan ourselves
    config.add_subscriber(prevent_csrf, NewRequest)
    config.add_subscriber(manage_stashes, NewRequest)
    config.add_subscriber(auto_privilege_escalation, ContextFound)
    config.add_subscriber(start_template_timer, BeforeRender)
    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_subscriber(flush_everything, NewResponse)
    config.add_subscriber(log_timers, NewResponse)

    floof.routing.configure_routing(config)
    config.scan(floof.views)

    app = config.make_wsgi_app()
    app = HTTPOnlyCookieMiddleware(app)
    return app

def compile_sass(root):
    """Compile raw Sass into regular ol' CSS.

    Skipped if FLOOF_SKIP_SASS_COMPILATION is set.
    """
    sass_paths = u':'.join((
        os.path.join(root, 'sass'),
        os.path.join(root, 'public', 'css'),
    ))

    # If this fails with a file not found, sass probably isn't installed
    # or in your path.  (gem install haml)
    subprocess.Popen(['sass',
        '--scss',
        '--style', 'compressed',
        '--stop-on-error',
        '--update', sass_paths,
    ]).wait()
