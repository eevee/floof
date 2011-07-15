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
    # Static file access
    config.add_static_view('/public', 'floof:public')

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
    r('art.view', r'/art/{id:\d+}{title:(;.+)?}', **kw)
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

    # XXX DO COMMENTS *LAST*, AND DO A COOL TRAVERSAL THING
    # XXX LAST.  I MEAN IT.


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
            return floof.model.meta.Session.query(sqla_column.parententity).filter(sqla_column == request.matchdict[match_key]).one()
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
        kw['title'] = ';' + _make_url_friendly(artwork.title)
    else:
        kw['title'] = ''

    return elements, kw

def _make_url_friendly(title):
    """Given a title that will be used as flavor text in a URL, returns a
    string that will look less like garbage in an address bar.
    """
    # RFC 3986 section 2.3 says: letters, numbers, and -_.~ are unreserved
    return re.sub('[^-_.~a-zA-Z0-9]', '-', title)
