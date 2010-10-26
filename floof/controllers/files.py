import logging
import errno

from pylons import config
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from floof.lib.base import BaseController, render

log = logging.getLogger(__name__)

class FilesController(BaseController):

    def view(self, key):
        storage = config['filestore']

        try:
            fileobj, info = storage.get(key)
        except IOError, e:
            if e.errno == errno.ENOENT:
                abort(404)
            else:
                raise

        mimetype = info.get('mimetype', 'application/octet-stream')
        response.content_type = mimetype

        if mimetype.startswith('text/'):
            response.charset = info.get('charset', None)
        else:
            response.charset = None

        # XXX sanitize filename?
        if 'filename' in info:
            response.content_disposition = \
                "attachment; filename=\"%s\"" % info['filename']

        return fileobj


