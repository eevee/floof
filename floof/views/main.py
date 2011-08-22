import logging
import urllib2

from sqlalchemy.orm.exc import NoResultFound
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response
from pyramid.view import view_config

from floof import model
from floof.model import meta

log = logging.getLogger(__name__)

@view_config(
    route_name='root',
    request_method='GET',
    renderer='index.mako')
def dummy_index(context, request):
    return {}


def wsgi_reproxy(url):
    """A WSGI response generator that will reproxy the contents of
    `url`.
    """
    fileish = urllib2.urlopen(url)
    while True:
        buf = fileish.read(512 * 1024)
        if not buf:
            break
        yield buf

@view_config(
    route_name='filestore',
    request_method='GET')
def filestore(context, request):
    """Serve a file from storage.

    If we appear to be downstream from a proxy and the storage supports it,
    this method will return an empty response body with headers indicating
    the "real" location of the file.  Otherwise, we'll respond with the
    whole file.  The latter puts a terrible strain on the app and will spew
    warnings if not in debug mode.
    """
    class_ = request.matchdict['class_']
    key = request.matchdict['key']

    storage = request.registry.settings['filestore']
    storage_url = storage.url(class_, key)
    if not storage_url:
        # No such file, oh dear
        log.warn("File {0} is missing".format(key))
        raise NotFound()

    # Get the MIME type and a filename
    # TODO this is surely not the most reliable way of doing this.
    headerlist = []
    if class_ in (u'thumbnail', u'artwork'):
        try:
            artwork = meta.Session.query(model.Artwork) \
                .filter_by(hash=key) \
                .one()
        except NoResultFound:
            raise NotFound()

        headerlist.append(('Content-Type', artwork.mime_type))

        # Don't bother setting disposition for thumbnails
        if class_ == u'artwork':
            mtime_rfc822 = artwork.uploaded_time.strftime(
                "%a, %d %b %Y %H:%M:%S %Z")
            headerlist.append((
                'Content-Disposition',
                'inline; filename={0}; modification-date="{1}";'.format(
                    artwork.filename.encode('utf8'), mtime_rfc822),
            ))
    else:
        # Unknown class
        raise NotFound()

    if 'X-Forwarded-For' in request.headers:
        # Reproxy to upstream.
        # nginx will only reproxy to local, internal URLs.  So this needs
        # something a bit special.  Tell nginx to reproxy to a special
        # nonexistent URL, and pass the actual target via the standard(?)
        # reproxy header

        # nginx, lighttpd, apache's mod_xsendfile
        # XXX replace with route_url
        headerlist.append(('X-Accel-Redirect', "/reproxy"))

        # perlbal, apache's mod_reproxy
        headerlist.append(('X-Reproxy-URL', storage_url))

        return Response(headerlist=headerlist)


    # Otherwise, we need to stream the whole file ourselves.  Ick.
    if not request.registry.settings['super_debug']:
        log.warn("Manually serving a file from storage; "
            "this is not what you want in production!")
    return Response(
        app_iter=wsgi_reproxy(storage_url),
        headerlist=headerlist,
    )


@view_config(
    route_name='reproxy',
    request_method='GET')
def reproxy(context, request):
    """This is a bogus URL used for nginx reproxying.  Clients should never
    land here!
    """
    log.warn("Client landed on /reproxy; your upstream is misconfigured!")
    return Response(
        body="our apologies; app misconfiguration",
        headerlist=[('Content-type', 'text/plain; charset=utf-8')],
    )


@view_config(
    route_name='cookies_disabled',
    request_method='GET',
    renderer='cookies_disabled.mako')
def cookies_disabled(context, request):
    if request.cookies:
        # Something odd has happened, but the "you've got cookies
        # disabled" message is clearly inappropriate here.
        return HTTPSeeOther(location=request.route_url('account.login'))

    return dict()


@view_config(
    route_name='log',
    request_method='GET',
    renderer='log.mako')
def view_log(context, request):
    records = meta.Session.query(model.Log) \
        .offset(0) \
        .limit(50)
    return dict(
        records=records,
    )
