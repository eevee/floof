from pyramid_beaker import session_factory_from_settings
from pyramid import security
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.request import Request
from sqlalchemy import engine_from_config

from floof.lib.auth import Authenticizer, FloofAuthPolicy
from floof.model import User, filestore, meta

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
    ### Settings
    engine = engine_from_config(settings, 'sqlalchemy.')

    import floof.model
    from zope.sqlalchemy import ZopeTransactionExtension
    floof.model.meta.Session.configure(bind=engine, extension=ZopeTransactionExtension())
    floof.model.TableBase.metadata.bind = engine                             

    settings['filestore'] = filestore.get_storage(settings)

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
    config.add_route('filestore', '/filestore/{class_}/{key}')
    config.add_route('reproxy', '/reproxy')
    config.add_route('cookies_disabled', '/cookies_disabled')
    config.add_route('log', '/log')

    # Registration and auth
    config.add_route('account.login', '/account/login')
    config.add_route('account.login_begin', '/account/login_begin')
    config.add_route('account.login_finish', '/account/login_finish')
    config.add_route('account.register', '/account/register')
    config.add_route('account.logout', '/account/logout')

    config.add_route('account.profile', '/account/profile')

    # Regular user control panel
    config.add_route('controls.index', '/account/controls')
    config.add_route('controls.auth', '/account/controls/authentication')
    config.add_route('controls.openid', '/account/controls/openid')
    config.add_route('controls.openid.add', '/account/controls/openid/add')
    config.add_route('controls.openid.add_finish', '/account/controls/openid/add_finish')
    config.add_route('controls.openid.remove', '/account/controls/openid/remove')
    config.add_route('controls.rels', '/account/controls/relationships')
    config.add_route('controls.rels.watch', '/account/controls/relationships/watch')
    config.add_route('controls.rels.unwatch', '/account/controls/relationships/unwatch')
    config.add_route('controls.info', '/account/controls/user_info')

    config.add_route('controls.certs', '/account/controls/certificates')
    config.add_route('controls.certs.generate_server', '/account/controls/certificates/gen/cert-{name}.p12')
    config.add_route('controls.certs.details', '/account/controls/certificates/details/{id}')
    config.add_route('controls.certs.download', '/account/controls/certificates/download/cert-{name}-{id}.pem')
    config.add_route('controls.certs.revoke', '/account/controls/certificates/revoke/{id}')

    # User pages
    config.add_route('users.view', '/users/{name}')
    config.add_route('users.art_by_label', '/users/{name}/art/{label}')
    config.add_route('users.profile', '/users/{name}/profile')
    config.add_route('users.watchstream', '/users/{name}/watchstream')

    # Art
    config.add_route('art.browse', '/art')
    config.add_route('art.upload', '/art/upload')

    def pregen_artwork_url(request, elements, kw):
        # XXX is this check even necessary?  why would artwork not be there?
        # XXX can we extend this thing to all the /art/## urls using modely context stuff?
        if 'artwork' in kw:
            artwork = kw['artwork']
            kw['id'] = artwork.id
            if artwork.title:
                # TODO _make_url_friendly
                kw['title'] = ';' + artwork.title
            else:
                kw['title'] = ''

        return elements, kw

    config.add_route('art.view', r'/art/{id:\d+}{title:(;.+)?}', pregenerator=pregen_artwork_url)
    config.add_route('art.add_tags', r'/art/{id:\d+}/add_tags')
    config.add_route('art.remove_tags', r'/art/{id:\d+}/remove_tags')
    config.add_route('art.rate', r'/art/{id:\d+}/rate')

    # XXX DO COMMENTS *LAST*, AND DO A COOL TRAVERSAL THING
    # XXX LAST.  I MEAN IT.

    #map.connect('', controller='controls', action='index')
    #map.connect('/{action}', controller='controls', requirements=dict(action='authentication|certificates|openid|relationships|user_info'))
    #map.connect('/certificates/gen/cert-{name}.p12', controller='controls', action='certificates_server', **require_POST)
    #map.connect('/certificates/details/{id}', controller='controls', action='certificates_details', **require_GET)
    #map.connect('/certificates/download/cert-{name}-{id}.pem', controller='controls', action='certificates_download', **require_GET)
    #map.connect('/certificates/revoke/{id}', controller='controls', action='certificates_revoke')
    #map.connect('/relationships/watch', controller='controls', action='relationships_watch', **require_GET)
    #map.connect('/relationships/watch', controller='controls', action='relationships_watch_commit', **require_POST)
    #map.connect('/relationships/unwatch_commit', controller='controls', action='relationships_unwatch_commit', **require_POST)


    import floof.views
    config.scan(floof.views)
    return config.make_wsgi_app()
