"""Abstracts away file storage and retrieval.

It's not uncommon to want to switch between a local filesystem or mogilefs or
some kind of cloud thing, and that's a pain when the relevant code is strewn
everywhere.  So, this class is a wrapper around the operations needed on
uploaded files.  It also provides the necessary machinery to be used with a
transaction manager.

Files are all identified by `class_`, a sort of rough category or namespace,
and `key`, which is just an identifier.  For example, with local storage, files
are stored under ``/class_/k/e/y/key``.

A storage object factory can be retrieved through :func:`get_storage_factory`.
"""

from __future__ import absolute_import
from cStringIO import StringIO
import shutil

from pyramid.util import DottedNameResolver
import transaction


def get_storage_factory(settings, prefix='filestore'):
    """Uses a Pyramid deployment settings dictionary to construct and return
    an instance of a :class:`FileStorage` subclass.

    The `prefix` will be used to extract storage configuration.  The package to
    use is determined by the `$prefix` config setting, and any setting named
    `$prefix.$key` will be passed to the subclass constructor as `$key`.

    The `$prefix` config setting may be either the full dotted python name of a
    data manager class, or the name of one of the modules in the
    floof.model.filestore namespace, currently `local` or `mogilefs`.
    """
    # Pull prefix.key out of the config object
    kwargs = {}
    plen = len(prefix)
    for key, val in settings.iteritems():
        if key[0:plen] == prefix and len(key) > plen:
            kwargs[ key[plen+1:] ] = val

    # Resolve the data manager
    resolver = DottedNameResolver(None)
    manager = settings[prefix]
    name = 'floof.model.filestore.' + manager + '.FileStorage'
    try:
        storage = resolver.resolve(name)
    except ImportError:
        storage = resolver.resolve(manager)

    def storage_factory():
        """Returns an instance of the chosen data manager for attachement to a
        request object and use over the life of a single request.  The instance
        must be manually joined to a Zope-style transaction."""
        return storage(transaction.manager, **kwargs)

    return storage_factory


# TODO: several steps here
# 3. add notion of file class for all filestorages; local can either ignore or use subdirectories
# fix this impl-per-module nonsense
class FileStorage(object):
    """Implements a staging dictionary to temporarily hold in StringIO objects
    copies of all file objects that are passed to :meth`put`.

    Child classes must implement :meth:`url` and the Zope transaction `data
    manager` methods according to their actual backends.

    See: http://www.zodb.org/zodbbook/transactions.html

    """
    def __init__(self, transaction_manager, **kwargs):
        self.transaction_manager = transaction_manager
        self.stage = {}

    def put(self, class_, key, fileobj):
        """Stages the data in the `fileobj` for subsequent commital under the
        given `class_` and `key`."""

        stageobj = StringIO()
        shutil.copyfileobj(fileobj, stageobj)
        fileobj.seek(0)
        stageobj.seek(0)

        idx = self._idx(class_, key)
        self.stage[idx] = (class_, key, stageobj)

    def _idx(self, class_, key):
        """Index for use in the staging dict."""
        return u':'.join((class_, key))

    def _finish(self):
        """Cleans up the temporary memory file storage.

        Should be run at the end of any abort or commit, regardless of the
        outcome.  (i.e. at the end of :meth:`abort`, :meth:`tpc_finish` and
        :meth:`tpc_abort`.)
        """
        self.stage = {}

    def sortKey(self):
        """Return a string by which to sort the commit order for transactions
        with multiple data managers."""
        return 'filestore:{0}'.format(id(self.stage))

    def url(self, class_, key):
        """Returns a URL for accessing this file.

        Must be a fully-qualified URL, or None if the file doesn't seem to
        exist.  Local files can be served by using file:// URLs.
        """
        raise NotImplementedError

    def abort(self, transaction):
        """Run if the transaction is aborted before the two-stage commit
        process begins."""
        raise NotImplementedError

    def tpc_begin(self, transaction):
        """Run at the start of the two-tage commit."""
        raise NotImplementedError

    def commit(self, transaction):
        """Run during the two-tage commit process; should commit the files
        non-permanently."""
        raise NotImplementedError

    def tpc_vote(self, transaction):
        """Run during the two-tage commit process; should raise an exception if
        the commit process should abort."""
        raise NotImplementedError

    def tpc_finish(self, transaction):
        """Run at the successful completion of the two-stage commit process.
        Should strenuously avoid failing."""
        raise NotImplementedError

    def tpc_abort(self, transaction):
        """Run if the two-tage commit process is aborted.  Should not fail."""
        raise NotImplementedError
