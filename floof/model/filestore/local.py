"""Local file storage."""

from __future__ import absolute_import

import os
import os.path
import shutil

from pylons import url

from . import FileStorage as BaseFileStorage

# XXX how on earth will this handle mimetypes correctly?!
# do files need to actually be separate database objects?  :(
class FileStorage(BaseFileStorage):
    def __init__(self, directory, url_prefix, **kwargs):
        if not os.path.isdir(directory):
            raise IOError("Directory {0} does not exist.".format(directory))

        self.directory = directory
        self.url_prefix = url_prefix

    def put(self, key, fileobj):
        dest = open(os.path.join(self.directory, key), 'wb')
        shutil.copyfileobj(fileobj, dest)
        
    def url(self, key, maxsize=None):
        return url("{0}/{1}".format(self.url_prefix, key))
