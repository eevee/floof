"""Routing configuration, broken out separately for ease of consultation
without going through the whole app config everything.

Some useful helpers are at the bottom.  Be familiar with them!
"""
import re

import floof.model
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
    r('filestore', '/filestore/{class_}/{key}')
    r('reproxy', '/reproxy')
    r('cookies_disabled', '/cookies_disabled')
    r('log', '/log')

    # Registration and auth
    r('account.login', '/account/login')
    r('account.login_begin', '/account/login_begin')
    r('account.login_finish', '/account/login_finish')
    r('account.register', '/account/register')
    r('account.add_identity', '/account/add_identity')
    r('account.logout', '/account/logout')

    r('account.profile', '/account/profile')

    # Regular user control panel
    r('controls.index', '/account/controls')
    r('controls.auth', '/account/controls/authentication')
    r('controls.openid', '/account/controls/openid')
    r('controls.openid.add', '/account/controls/openid/add')
    r('controls.openid.add_finish', '/account/controls/openid/add_finish')
    r('controls.openid.remove', '/account/controls/openid/remove')
    r('controls.rels', '/account/controls/relationships')
    r('controls.rels.watch', '/account/controls/relationships/watch')
    r('controls.rels.unwatch', '/account/controls/relationships/unwatch')
    r('controls.info', '/account/controls/user_info')

    r('controls.certs', '/account/controls/certificates')
    r('controls.certs.generate_server', '/account/controls/certificates/gen/cert-{name}.p12')
    r('controls.certs.details', '/account/controls/certificates/details/{id}')
    r('controls.certs.download', '/account/controls/certificates/download/cert-{name}-{id}.pem')
    r('controls.certs.revoke', '/account/controls/certificates/revoke/{id}')

    # User pages
    kw = sqla_route_options('user', 'name', floof.model.User.name)
    r('users.view', '/users/{name}', **kw)
    r('users.art_by_label', '/users/{name}/art/{label}', **kw)
    r('users.profile', '/users/{name}/profile', **kw)
    r('users.watchstream', '/users/{name}/watchstream', **kw)

    # Artwork
    kw = sqla_route_options('artwork', 'id', floof.model.Artwork.id)
    kw['pregenerator'] = artwork_pregenerator
    r('art.browse', '/art')
    r('art.upload', '/art/upload')
    r('art.view', r'/art/{id:\d+}{title:(!.+)?}', **kw)
    r('art.add_tags', r'/art/{id:\d+}/add_tags', **kw)
    r('art.remove_tags', r'/art/{id:\d+}/remove_tags', **kw)
    r('art.rate', r'/art/{id:\d+}/rate', **kw)

    # Tags
    # XXX what should the tag name regex be, if anything?
    # XXX should the regex be checked in the 'factory' instead?  way easier that way...
    kw = sqla_route_options('tag', 'name', floof.model.Tag.name)
    r('tags.list', '/tags')
    r('tags.view', '/tags/{name}', **kw)
    r('tags.artwork', '/tags/{name}/artwork', **kw)

    # Administration
    r('admin.dashboard', '/admin')
    r('admin.log', '/admin/log')

    # Debugging
    r('debug.blank', '/debug/blank')
    r('debug.crash', '/debug/crash')
    r('debug.status.303', '/debug/303')
    r('debug.status.400', '/debug/400')
    r('debug.status.403', '/debug/403')
    r('debug.status.404', '/debug/404')

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
        users=floof.model.User.name,
        art=floof.model.Artwork.id,
    )

    def comments_factory(request):
        # XXX prefetching on these?
        type = request.matchdict['type']
        identifier = request.matchdict['identifier']

        try:
            sqla_column = commentables[type]
            entity = floof.model.session.query(sqla_column.parententity).filter(sqla_column == identifier).one()
        except (NoResultFound, KeyError):
            # 404!
            raise NotFound()

        if 'comment_id' not in request.matchdict:
            return entity.discussion

        # URLs to specific comments should have those comments as the context
        try:
            return floof.model.session.query(floof.model.Comment).with_parent(entity.discussion).filter(floof.model.Comment.id == request.matchdict['comment_id']).one()
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
    r('comments.reply', '/{type}/{identifier}/comments/{comment_id}/write', factory=comments_factory, pregenerator=comments_pregenerator)

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
            return floof.model.session.query(sqla_column.parententity).filter(sqla_column == request.matchdict[match_key]).one()
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
        kw['title'] = '!' + _make_url_friendly(artwork.title)
    else:
        kw['title'] = ''

    return elements, kw

def _make_url_friendly(title):
    """Given a title that will be used as flavor text in a URL, returns a
    string that will look less like garbage in an address bar.
    """
    # RFC 3986 section 2.3 says: letters, numbers, and -_.~ are unreserved
    return re.sub('[^-_.~a-zA-Z0-9]', '-', title)
