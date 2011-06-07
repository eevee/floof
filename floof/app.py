from pyramid_beaker import session_factory_from_settings
from pyramid import security
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.request import Request
from sqlalchemy import engine_from_config

from floof.model import User, meta

def renderer_globals_factory(system):
    import floof.lib.helpers
    import floof.model
    import collections
    import pyramid.url
    user = object()
    class Auth(object):
        def can_purge(self, *a, **kw):
            return False
    auth = Auth()
    auth.pending_user = None

    import pyramid.security

    return dict(
        h=floof.lib.helpers,
        config=collections.defaultdict(unicode),
        user=system['request'].user,
        auth=auth,
        timer=object(),
        url=lambda *a, **kw: repr(a) + repr(kw),

        static_url=lambda path: pyramid.url.static_url(path, system['request']),
    )

class FloofRequest(Request):
    @reify
    def user(self):
        # XXX I don't like any of this wackiness tbh
        user_id = security.unauthenticated_userid(self)
        import floof.model
        if user_id is None:
            return floof.model.AnonymousUser()

        return meta.Session.query(User).filter_by(id=user_id).one()

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
        authentication_policy=AuthTktAuthenticationPolicy(
            secret='secret',  # XXX
            timeout=1800,  # expiration
            reissue_time=180,
            max_age=1800,
            http_only=True,
            wild_domain=False,
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
