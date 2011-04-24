import logging
import urllib2
import warnings

from pylons import config, request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort

from floof.lib.base import BaseController, render
from floof.lib.helpers import redirect
from floof.lib.log import ADMIN
from floof import model
from floof.model import meta, Log

log = logging.getLogger(__name__)

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

class MainController(BaseController):

    def index(self):
        return render('/index.mako')

    def filestore(self, key):
        """Serve a file from storage.

        If we appear to be downstream from a proxy and the storage supports it,
        this method will return an empty response body with headers indicating
        the "real" location of the file.  Otherwise, we'll respond with the
        whole file.  The latter puts a terrible strain on the app and will spew
        warnings if not in debug mode.
        """
        storage = config['filestore']
        storage_url = storage.url(key)
        if not storage_url:
            # No such file, oh dear
            log.warn("File {0} is missing".format(key))
            abort(404)

        if storage_url.startswith(u'/'):
            # Absolute paths are relative to the application
            storage_url = url(storage_url)

        # TODO this is totally wrong, but at least less so.  how can we
        # reliably get the mimetype for any file hash?  new table?
        response.headers['Content-Type'] = 'image/png'

        if 'X-Forwarded-For' in request.headers:
            # Reproxy to upstream.
            # nginx will only reproxy to local, internal URLs.  So this needs
            # something a bit special.  Tell nginx to reproxy to a special
            # nonexistent URL, and pass the actual target via the standard(?)
            # reproxy header

            # nginx, lighttpd, apache's mod_xsendfile
            response.headers['X-Accel-Redirect'] = "/reproxy"

            # perlbal, apache's mod_reproxy
            response.headers['X-Reproxy-URL'] = storage_url

            return None

        # Otherwise, we need to stream the whole file ourselves.  Ick.
        if not config['super_debug']:
            log.warn("Manually serving a file from storage; "
                "this is not what you want in production!")
        return wsgi_reproxy(storage_url)

    def reproxy(self):
        """This is a bogus URL used for nginx reproxying.  Clients should never
        land here!
        """
        log.warn("Client landed on /reproxy; your upstream is misconfigured!")
        return "our apologies; app misconfiguration"

    def cookies_disabled(self):
        if request.cookies:
            # Something odd has happened, but the "you've got cookies
            # disabled" message is clearly inappropriate here.
            redirect(url(controller='account', action='login'))
        return render('/cookies_disabled.mako')

    def log(self):
        c.records = meta.Session.query(model.Log) \
            .filter_by(level=ADMIN) \
            .offset(0) \
            .limit(50)
        return render('/log.mako')
