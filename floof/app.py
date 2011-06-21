from pyramid_beaker import session_factory_from_settings
from pyramid import security
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.request import Request
from sqlalchemy import engine_from_config

from floof.lib.auth import Authenticizer, FloofAuthPolicy
from floof.model import User, meta

def renderer_globals_factory(system):
    import floof.lib.helpers
    import floof.model
    import collections
    import pyramid.url
    user = object()

    import pyramid.security

    return dict(
        h=floof.lib.helpers,
        config=collections.defaultdict(unicode),
        user=system['request'].user,
        auth=system['request'].auth,  # XXX should be getting rid of this, probably
        timer=object(),
        url=lambda *a, **kw: repr(a) + repr(kw),

        static_url=lambda path: pyramid.url.static_url(path, system['request']),
    )


class FloofRequest(Request):
    @reify
    def auth(self):
        auth = Authenticizer(self)
        self.session.changed()
        return auth

    @property
    def user(self):
        return self.auth.user


def main(global_config, **settings):
    """Constructs a WSGI application."""
    engine = engine_from_config(settings, 'sqlalchemy.')

    import floof.model
    from zope.sqlalchemy import ZopeTransactionExtension
    floof.model.meta.Session.configure(bind=engine, extension=ZopeTransactionExtension())
    floof.model.TableBase.metadata.bind = engine                             

    config = Configurator(
        settings=settings,
        request_factory=FloofRequest,
        session_factory=session_factory_from_settings(settings),
        authentication_policy=FloofAuthPolicy(
            # TODO move this stuff to beaker support
            #secret='secret',  # XXX
            #timeout=1800,  # expiration
            #reissue_time=180,
            #max_age=1800,
            #http_only=True,
            #wild_domain=False,
            #secure=True,
        ),
        renderer_globals_factory=renderer_globals_factory,
    )
    config.add_static_view('/public', 'floof:public')

    ### Routing
    config.add_route('root', '/')

    # Registration and auth
    config.add_route('account.login', '/account/login')
    config.add_route('account.login_begin', '/account/login_begin')
    config.add_route('account.login_finish', '/account/login_finish')
    config.add_route('account.register', '/account/register')
    config.add_route('account.logout', '/account/logout')

    config.add_route('account.profile', '/account/profile')


    import floof.views
    config.scan(floof.views)
    return config.make_wsgi_app()
