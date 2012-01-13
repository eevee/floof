"""Store files in MogileFS."""

from __future__ import absolute_import

import logging
import shutil
import uuid

import pymogile

from floof.model.filestore import FileStorage as BaseFileStorage

log = logging.getLogger(__name__)


class FileStorage(BaseFileStorage):
    """

    Note that :meth:`url` cannot know the URL to a newly :meth`put` file until
    the transaction has been commited.

    """
    def __init__(self, transaction_manager, domain, trackers, **kwargs):
        super(FileStorage, self).__init__(transaction_manager, **kwargs)

        trackers = trackers.split()
        self.client = pymogile.Client(domain=domain, trackers=trackers)
        self.temp = []

    def url(self, class_, key):
        ident = self._identifier(class_, key)
        paths = self.client.get_paths(ident, pathcount=1)

        if paths:
            return paths[0]
        else:
            return None

    def _identifier(self, class_, key):
        """Use class:key as the identifier within mogile."""
        return u':'.join((class_, key))

    def _finish(self):
        self.temp = []
        super(FileStorage, self)._finish()

    def abort(self, transaction):
        self._finish()

    def tpc_begin(self, transaction):
        pass

    def commit(self, transaction):
        for class_, key, stageobj in self.stage.itervalues():
            # Can't use store_file here; it very rudely closes the file when it's done
            ident = self._identifier(class_, key)
            rand = uuid.uuid4().hex
            tempident = u':'.join(('__temp__', ident, rand))
            self.temp.append((ident, tempident))
            with self.client.new_file(tempident, cls=class_) as f:
                shutil.copyfileobj(stageobj, f)

    def tpc_vote(self, transaction):
        pass

    def tpc_finish(self, transaction):
        for ident, tempident in self.temp:
            self.client.rename(tempident, ident)
        self._finish()

    def tpc_abort(self, transaction):
        for ident, tempident in self.temp:
            try:
                self.client.delete(tempident)
            except:
                log.error("Failed to delete orphaned file '{0}' "
                          "during transaction abort".format(tempident))
        self._finish()
