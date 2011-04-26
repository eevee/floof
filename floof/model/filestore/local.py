"""Local file storage."""

from __future__ import absolute_import

import os
import os.path
import shutil

from . import FileStorage as BaseFileStorage

class FileStorage(BaseFileStorage):
    def __init__(self, directory, **kwargs):
        if not os.path.isdir(directory):
            raise IOError("filestore.directory {0} does not exist".format(directory))

        self.directory = directory

    def _path(self, prefix, class_, key):
        """Store the file under class/k/e/y/key."""
        long_key = key + '__'
        return os.path.join(
            prefix, class_,
            long_key[0], long_key[1], long_key[2], key)

    def put(self, class_, key, fileobj):
        dest = self._path(self.directory, class_, key)
        dest_dir, _ = os.path.split(dest)

        if not os.exists(dest_dir):
            os.makedirs(dest_dir)

        with os.fdopen(os.open(dest, os.O_WRONLY | os.O_CREAT, 0644), 'wb') as destobj:
            shutil.copyfileobj(fileobj, destobj)

    def url(self, class_, key):
        return 'file://' + self._path(self.directory, class_, key).encode('utf8')
