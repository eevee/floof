"""Store files in MogileFS."""

from __future__ import absolute_import

import os
import os.path
import shutil

from pylons import url
import pymogile

from . import FileStorage as BaseFileStorage

# XXX how on earth will this handle mimetypes correctly?!
# do files need to actually be separate database objects?  :(
class FileStorage(BaseFileStorage):
    def __init__(self, domain, trackers, **kwargs):
        trackers = trackers.split()

        self.client = pymogile.Client(domain=domain, trackers=trackers)

    def put(self, key, fileobj):
        class_ = 'artwork'
        self.client.store_file(key, fileobj, cls=class_)

    def url(self, key):
        class_ = 'artwork'
        paths = self.client.get_paths(key, pathcount=1)
        print paths
        if paths:
            return paths[0]
        else:
            return "/nowhere"  # XXX need a special URL to a dummy file
