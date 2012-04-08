"""Routing configuration, broken out separately for ease of consultation
without going through the whole app config everything.

Some useful helpers are at the bottom.  Be familiar with them!
"""
import re

import floof.model as model
from floof.resource import contextualize
from pyramid.exceptions import NotFound
from sqlalchemy.orm.exc import NoResultFound

def configure_routing(config):
    """Adds route declarations to the app config."""
    # Static file access.  Separate root for each subdirectory, because Pyramid
    # treats these as first-class routables rather than a last-ditch fallback
    config.add_static_view('/css', 'floof:public/css')
    config.add_static_view('/files', 'floof:public/files')  # dummy file store
    config.add_static_view('/icons', 'floof:public/icons')
    config.add_static_view('/images', 'floof:public/images')
    config.add_static_view('/js', 'floof:public/js')
    # TODO this doesn't actually work
    config.add_static_view('/favicon.ico', 'floof:public/favicon.ico')


    r = config.add_route

    # Miscellaneous root stuff
    r('root', '/')
    r('filestore', '/filestore/{class_}/{key}', pregenerator=filestore_pregenerator)
    r('reproxy', '/reproxy')
    r('log', '/log')

    # Registration and auth
    r('account.login', '/account/login')
    r('account.login_begin', '/account/login_begin')
    r('account.login_finish', '/account/login_finish')
    r('account.register', '/account/register')
    r('account.add_identity', '/account/add_identity')
    r('account.browserid.login', '/account/browserid/login')
    r('account.logout', '/account/logout')

    r('account.profile', '/account/profile')

    # Regular user control panel
    r('controls.index', '/account/controls')
    r('controls.auth', '/account/controls/authentication')
    r('controls.browserid', '/account/controls/browserid')
    r('controls.browserid.add', '/account/controls/browserid/add')
    r('controls.browserid.remove', '/account/controls/browserid/remove')
    r('controls.openid', '/account/controls/openid')
    r('controls.openid.add', '/account/controls/openid/add')
    r('controls.openid.add_finish', '/account/controls/openid/add_finish')
    r('controls.openid.remove', '/account/controls/openid/remove')
    r('controls.rels', '/account/controls/relationships')
    r('controls.rels.watch', '/account/controls/relationships/watch')
    r('controls.rels.unwatch', '/account/controls/relationships/unwatch')
    r('controls.info', '/account/controls/user_info')

    r('controls.certs', '/account/controls/certificates')
    r('controls.certs.add', '/account/controls/certificates/add')
    r('controls.certs.generate_server',
            '/account/controls/certificates/gen/cert-{name}.p12')
    r('controls.certs.details',
            '/account/controls/certificates/details/{serial:[0-9a-f]+}')
    r('controls.certs.download',
            '/account/controls/certificates/download/cert-{name}-{serial:[0-9a-f]+}.pem')
    r('controls.certs.revoke',
            '/account/controls/certificates/revoke/{serial:[0-9a-f]+}')

    # User pages
    kw = sqla_route_options('user', 'name', model.User.name)
    r('users.view', '/users/{name}', **kw)
    r('users.art_by_label', '/users/{name}/art/{label}', **kw)
    r('users.profile', '/users/{name}/profile', **kw)
    r('users.watchstream', '/users/{name}/watchstream', **kw)
    r('labels.user_index', '/users/{name}/labels', **kw)

    # Artwork
    kw = sqla_route_options('artwork', 'id', model.Artwork.id)
    kw['pregenerator'] = artwork_pregenerator
    r('art.browse', '/art')
    r('art.upload', '/art/upload')
    r('art.view', r'/art/{id:\d+}{title:(-.+)?}', **kw)
    r('art.add_tags', r'/art/{id:\d+}/add_tags', **kw)
    r('art.remove_tags', r'/art/{id:\d+}/remove_tags', **kw)
    r('art.rate', r'/art/{id:\d+}/rate', **kw)

    # Tags
    # XXX what should the tag name regex be, if anything?
    # XXX should the regex be checked in the 'factory' instead?  way easier that way...
    kw = sqla_route_options('tag', 'name', model.Tag.name)
    r('tags.list', '/tags')
    r('tags.view', '/tags/{name}', **kw)
    r('tags.artwork', '/tags/{name}/artwork', **kw)

    # Labels
    # XXX well this is getting complicated!  needs to check user, needs to check id, needs to generate correctly, needs a title like art has
    user_router = SugarRouter(config, '/users/{user}', model.User.name)
    label_router = user_router.chain('/labels/{label}', model.Label.id, rel=model.Label.user)
    label_router.add_route('labels.artwork', '')

    # Administration
    r('admin.dashboard', '/admin')
    r('admin.log', '/admin/log')

    # Debugging
    r('debug.blank', '/debug/blank')
    r('debug.crash', '/debug/crash')
    r('debug.mako-crash', '/debug/mako-crash')
    r('debug.status.303', '/debug/303')
    r('debug.status.400', '/debug/400')
    r('debug.status.403', '/debug/403')
    r('debug.status.404', '/debug/404')

    # API - Art
    kw = sqla_route_options('artwork', 'id', model.Artwork.id)
    r('api.art.browse', '/api/art')
    r('api.art.browse.page', '/api/art/{page:\d+}')
    r('api.art.view', '/api/art/{id}', **kw)

    # API - User
    kw = sqla_route_options('user', 'name', model.User.name)
    r('api.users.view', '/api/users/{name}', **kw)
    r('api.users.user_index', '/api/users/{name}/labels', **kw)
    r('api.users.watchstream', '/api/users/{name}/watchstream', **kw)
    # Not implemented because not in use or regular implementation is broken
    # r('api.users.profile', '/api/users/{name}/profile', **kw)
    # r('api.users.art_by_label', '/api/users/{name}/art/{label}', **kw)

    # API - Tags
    kw = sqla_route_options('tag', 'name', model.Tag.name)
    r('api.tags.list', '/api/tags')
    r('api.tags.view', '/api/tags/{name}', **kw)
    r('api.tags.artwork', '/api/tags/{name}/artwork', **kw)

    # Comments; made complex because they can attach to different parent URLs.
    # Rather than hack around how Pyramid's routes works, we can just use our
    # own class that does what we want!

    # XXX 1: make this work for users as well
    # XXX 2: make the other routes work
    # XXX 3: possibly find a way to verify that the same logic is used here and for the main routes
    parent_route_names = ('art.view', 'user.view')
    mapper = config.get_routes_mapper()
    parent_routes = [mapper.get_route(name) for name in parent_route_names]
    commentables = dict(
        users=model.User.name,
        art=model.Artwork.id,
    )

    def comments_factory(request):
        # XXX prefetching on these?
        type = request.matchdict['type']
        identifier = request.matchdict['identifier']

        try:
            sqla_column = commentables[type]
            entity = model.session.query(sqla_column.parententity).filter(sqla_column == identifier).one()
        except (NoResultFound, KeyError):
            # 404!
            raise NotFound()

        if 'comment_id' not in request.matchdict:
            return contextualize(entity.discussion)

        # URLs to specific comments should have those comments as the context
        try:
            return contextualize(
                model.session .query(model.Comment)
                .with_parent(entity.discussion)
                .filter(model.Comment.id == request.matchdict['comment_id'])
                .one())
        except NoResultFound:
            raise NotFound()


    def comments_pregenerator(request, elements, kw):
        resource = None
        comment = kw.get('comment', None)

        if comment:
            kw['comment_id'] = comment.id

            if 'resource' not in kw:
                resource = comment.discussion.resource

        if not resource:
            resource = kw['resource']

        # XXX users...
        entity = resource.member
        kw['type'] = 'art'
        kw['identifier'] = entity.id
        return elements, kw

    r('comments.list', '/{type}/{identifier}/comments', factory=comments_factory)
    r('comments.write', '/{type}/{identifier}/comments/write', factory=comments_factory, pregenerator=comments_pregenerator)
    r('comments.view', '/{type}/{identifier}/comments/{comment_id}', factory=comments_factory, pregenerator=comments_pregenerator)
    r('comments.edit', '/{type}/{identifier}/comments/{comment_id}/edit', factory=comments_factory, pregenerator=comments_pregenerator)
    r('comments.reply', '/{type}/{identifier}/comments/{comment_id}/write', factory=comments_factory, pregenerator=comments_pregenerator)

class SugarRouter(object):
    """Glues routing to the ORM.

    Use me like this:

        foo_router = SugarRouter(config, '/foos/{foo}', model.Foo.identifier)
        foo_router.add_route('foo_edit', '/edit')

    This will route `/foos/{foo}/edit` to `foo_edit`, with the bonus that the
    context will be set to the corresponding `Foo` object.

    The reverse works as well:

        request.route_url('foo_edit', foo=some_foo_row)
    """

    # TODO: support URLs like /art/123-title-that-doesnt-matter
    #       ...but only do it for the root url, i think

    def __init__(self, config, url_prefix, sqla_column, parent_router=None, rel=None):
        self.config = config
        self.url_prefix = url_prefix
        self.sqla_column = sqla_column
        self.sqla_table = sqla_column.parententity

        self.parent_router = parent_router
        self.sqla_rel = rel
        assert (self.parent_router is None) == (self.sqla_rel is None)

        # This is the {key} that appears in the matchdict and generated route,
        # as well as the kwarg passed to route_url
        match = re.search(r'[{](\w+)[}]', url_prefix)
        if not match:
            raise ValueError("Can't find a route kwarg in {0!r}".format(url_prefix))
        self.key = match.group(1)


    ### Dealing with chaining

    def chain(self, url_prefix, sqla_column, rel):
        """Create a new sugar router with this one as the parent."""
        return self.__class__(
            self.config, url_prefix, sqla_column,
            parent_router=self, rel=rel)

    @property
    def full_url_prefix(self):
        """Constructs a chain of url prefixes going up to the root."""
        if self.parent_router:
            ret = self.parent_router.full_url_prefix
        else:
            ret = ''

        ret += self.url_prefix
        return ret

    def filter_sqlalchemy_query(self, query, request):
        """Takes a query, filters it as demanded by the matchdict, and returns
        a new one.
        """
        query = query.filter(self.sqla_column == request.matchdict[self.key])

        if self.parent_router:
            query = query.join(self.sqla_rel)
            query = self.parent_router.filter_sqlalchemy_query(
                query, request)

        return query


    ### Actual routing stuff

    def add_route(self, route_name, suffix, **kwargs):
        """Analog to `config.add_route()`, with magic baked in.  Extra kwargs
        are passed along.
        """
        kwargs['pregenerator'] = self.pregenerator
        kwargs['factory'] = self.factory
        self.config.add_route(route_name, self.full_url_prefix + suffix, **kwargs)

    def pregenerator(self, request, elements, kw):
        """Passed to Pyramid as a bound method when creating a route.

        Converts the arguments to route_url (which should be row objects) into
        URL-friendly strings.
        """
        # Get the row object, and get the property from it
        row = kw.pop(self.key)
        kw[self.key] = self.sqla_column.__get__(row, type(row))

        if self.parent_router:
            # Parent needs its own treatment here, too.  Fill in the parent
            # object automatically
            kw[self.parent_router.key] = self.sqla_rel.__get__(row, type(row))
            elements, kw = self.parent_router.pregenerator(request, elements, kw)

        return elements, kw

    def factory(self, request):
        """Passed to Pyramid as a bound method when creating a route.

        Translates a matched URL to an ORM row, which becomes the context.
        """
        # This yields the "context", which should be the row object
        try:
            q = model.session.query(self.sqla_table)
            q = self.filter_sqlalchemy_query(q, request)
            return q.one()
        except NoResultFound:
            # 404!
            raise NotFound()


def sqla_route_options(url_key, match_key, sqla_column):
    """Returns a dict of route options that are helpful for routes representing SQLA objects.

    ``url_key``:
        The key to use for a SQLA object when calling ``route_url()``.

    ``match_key``:
        The key in the matchdict that contains the row identifier.

    ``sqla_column``:
        The SQLA ORM column that appears in the URL.
    """
    def pregenerator(request, elements, kw):
        # Get the row object, and get the property from it
        row = kw.pop(url_key)
        kw[match_key] = sqla_column.__get__(row, type(row))
        return elements, kw

    def factory(request):
        # This yields the "context", which should be the row object
        try:
            return contextualize(
                model.session.query(sqla_column.parententity)
                .filter(sqla_column == request.matchdict[match_key])
                .one())
        except NoResultFound:
            # 404!
            raise NotFound()

    return dict(pregenerator=pregenerator, factory=factory)

def artwork_pregenerator(request, elements, kw):
    """Special pregenerator for artwork URLs, which also include a title
    sometimes.
    """
    artwork = kw.pop('artwork')
    kw['id'] = artwork.id
    # n.b.: this won't hurt anything if the route doesn't have {title}, so it's
    # calculated and thrown away.  bad?
    if artwork.title:
        kw['title'] = '-' + _make_url_friendly(artwork.title)
    else:
        kw['title'] = ''

    return elements, kw

def _make_url_friendly(title):
    """Given a title that will be used as flavor text in a URL, returns a
    string that will look less like garbage in an address bar.
    """
    # RFC 3986 section 2.3 says: letters, numbers, and -_.~ are unreserved
    return re.sub('[^-_.~a-zA-Z0-9]', '-', title)

def filestore_pregenerator(request, elements, kw):
    """Pregenerator for the filestore, which may run under a different domain
    name in the case of a CDN cacher thinger.
    """
    cdn_root = request.registry.settings.get('cdn_root')
    if cdn_root:
        kw['_app_url'] = cdn_root

    return elements, kw
