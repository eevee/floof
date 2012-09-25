"""Local file storage."""

from __future__ import absolute_import

import logging
import os
import shutil
import tempfile

from floof.model.filestore import FileStorage as BaseFileStorage

log = logging.getLogger(__name__)


class FileStorage(BaseFileStorage):
    """FileStorage data manager using local files as a backend.

    This class tries hard to follow the Zope transaction manager interface,
    where :meth:`tpc_finish` should always succeed and only be reached if we
    are very confident that it will do so.

    """
    # XXX: This may be over-engineered.  If we only care about being able to
    # safely raise exceptions in view code, then it would be enough to just
    # write out the files once to their final location in :meth:`tpc_vote` and
    # set :meth:`sortKey` to return a string that will sort very low so that it
    # will run after SQLAlchemy.  This should leave orphan files only in the
    # case of local filesystem embuggerment.

    def __init__(self, transaction_manager, directory, **kwargs):
        super(FileStorage, self).__init__(transaction_manager, **kwargs)

        self.directory = directory
        if not os.path.isdir(directory):
            raise IOError("filestore.directory {0} does not exist".format(directory))

        self.tempdir = os.path.join(self.directory, '__temp__')
        if not os.path.isdir(self.tempdir):
            try:
                os.makedirs(self.tempdir)
            except OSError:
                if not os.path.isdir(self.tempdir):
                    raise IOError("Unable to make temporary directory '{0}'"
                                  .format(self.tempdir))

        self.tempfiles = {}

    def url(self, class_, key):
        return 'file://' + self._path(self.directory, class_, key).encode('utf8')

    def _path(self, prefix, class_, key):
        """Store the file under class/k/e/y/key."""
        long_key = key + '__'
        return os.path.join(
            prefix, class_,
            long_key[0], long_key[1], long_key[2], key)

    def _finish(self):
        self.tempfiles = {}
        super(FileStorage, self)._finish()

    def abort(self, transaction):
        self._finish()

    def tpc_begin(self, transaction):
        pass

    def commit(self, transaction):
        """Write the files out to a temporary directory; may catch some
        permission errors and filesystem capacity errors."""

        for idx, (class_, key, stageobj) in self.stage.iteritems():
            fd, path = tempfile.mkstemp(dir=self.tempdir)
            self.tempfiles[idx] = path
            fileobj = os.fdopen(fd, 'w')
            stageobj.seek(0)
            shutil.copyfileobj(stageobj, fileobj)
            fileobj.flush()
            fileobj.close()

    def tpc_vote(self, transaction):
        """Check that the destination directory exists and is writeable."""

        for idx, (class_, key, stageobj) in self.stage.iteritems():
            destpath = self._path(self.directory, class_, key)
            destdir, destfile = os.path.split(destpath)

            if not os.path.isdir(destdir):
                os.makedirs(destdir)

            if not os.access(destdir, os.W_OK | os.X_OK):
                raise IOError("Cannot traverse or cannot write to destination "
                              "directory '{0}'.".format(destdir))

    def tpc_finish(self, transaction):
        """Move the temporary files to their final location."""

        for idx, (class_, key, stageobj) in self.stage.iteritems():
            temppath = self.tempfiles[idx]
            destpath = self._path(self.directory, class_, key)
            shutil.move(temppath, destpath)

        self._finish()

    def tpc_abort(self, transaction):
        """Delete any orphaned temporary files, if possible."""

        for path in self.tempfiles.itervalues():
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    log.error("Failed to delete orphaned file '{0}' "
                              "during transaction abort".format(path))

        self._finish()
