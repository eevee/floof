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

    def _identifier(self, class_, key):
        """Use class:key as the identifier within mogile."""
        return u':'.join((class_, key))

    def put(self, class_, key, fileobj):
        # Can't use store_file here; it very rudely closes the file when it's done
        with self.client.new_file(
            self._identifier(class_, key), cls=class_) as f:

            shutil.copyfileobj(fileobj, f)

    def url(self, class_, key):
        paths = self.client.get_paths(
            self._identifier(class_, key), pathcount=1)

        if paths:
            return paths[0]
        else:
            return None
