from pyramid_beaker import session_factory_from_settings
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

def renderer_globals_factory(system):
    import floof.lib.helpers
    import floof.model
    import collections
    import pyramid.url
    user = object()
    class Auth(object): pass
    auth = Auth()
    auth.pending_user = None

    return dict(
        h=floof.lib.helpers,
        config=collections.defaultdict(unicode),
        user=floof.model.AnonymousUser(),
        auth=auth,
        timer=object(),
        url=lambda *a, **kw: repr(a) + repr(kw),

        static_url=lambda path: pyramid.url.static_url(path, system['request']),
    )

def main(global_config, **settings):
    """Constructs a WSGI application."""
    engine = engine_from_config(settings, 'sqlalchemy.')

    import floof.model
    from zope.sqlalchemy import ZopeTransactionExtension
    floof.model.meta.Session.configure(bind=engine, extension=ZopeTransactionExtension())
    floof.model.TableBase.metadata.bind = engine                             

    config = Configurator(
        settings=settings,
        session_factory=session_factory_from_settings(settings),
        renderer_globals_factory=renderer_globals_factory,
    )
    config.add_static_view('/public', 'floof:public')
    config.add_route('root', '/')
    import floof.views
    config.scan(floof.views)
    return config.make_wsgi_app()
