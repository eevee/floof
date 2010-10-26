"""Local file storage."""

from __future__ import absolute_import

import os
import os.path
import shutil
import errno
from xattr import xattr

from pylons import url

from . import FileStorage as BaseFileStorage

class FileStorage(BaseFileStorage):
    def __init__(self, directory, url_prefix, **kwargs):
        if not os.path.isdir(directory):
            raise IOError("Directory {0} does not exist.".format(directory))

        self.directory = directory
        self.url_prefix = url_prefix

    def put(self, key, fileobj, mimetype=None, filename=None):
        dest = open(os.path.join(self.directory, key), 'wb')
        shutil.copyfileobj(fileobj, dest)

        # If the filesystem does not support xattr, these will raise IOError;
        # might want to catch that, but for now i'm letting it probagate.
        attr = xattr(dest)
        if mimetype is not None:
            # see http://www.freedesktop.org/wiki/CommonExtendedAttributes
            attr['user.mime_type'] = mimetype
        if filename is not None:
            attr['user.floof.filename'] = filename

        dest.close()

    def get(self, key):
        fileobj = open(os.path.join(self.directory, key), 'rb')

        attr = xattr(fileobj)
        info = {}

        def copyattr(key, attrkey):
            try:
                info[key] = attr.get(attrkey)
            except IOError, e:
                # The manpage for getxattr(2) says that it raises ENOATTR if
                # the attribute is not found. ENOATTR is #defined as ENODATA
                # in xattr.h.
                if e.errno == errno.ENODATA:
                    pass
                else:
                    raise

        copyattr('mimetype', 'user.mime_type')
        copyattr('charset', 'user.charset')
        copyattr('filename', 'user.floof.filename')

        return fileobj, info

    def url(self, key, maxsize=None):
        return url("{0}/{1}".format(self.url_prefix, key))
