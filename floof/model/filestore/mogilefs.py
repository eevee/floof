"""Store files in MogileFS."""

from __future__ import absolute_import

import os
import os.path
import shutil

import pymogile

from . import FileStorage as BaseFileStorage

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
        if paths:
            return paths[0]
        else:
            return None
