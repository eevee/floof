"""Abstracts away file storage and retrieval.

It's not uncommon to want to switch between a local filesystem or mogilefs or
some kind of cloud thing, and that's a pain when the relevant code is strewn
everywhere.  So, this class is a simple wrapper around the operations needed on
uploaded files.

Files are all identified by 'key', which is just an identifier.  For example,
with local storage, it becomes the filename.

A storage object can be constructed with the `get_storage` function.
"""

from __future__ import absolute_import

def get_storage(pylons_config, prefix='filestore'):
    """Uses the Pylons configuration to construct and return an instance of a
    `FileStorage` subclass.

    The `prefix` will be used to extract storage configuration.  The package to
    use is determined by the `$prefix` config setting, and any setting named
    `$prefix.$key` will be passed to the subclass constructor as `$key`.
    """
    # Pull prefix.key out of the config object
    kwargs = {}
    plen = len(prefix)
    for key, val in pylons_config.iteritems():
        if key[0:plen] == prefix and len(key) > plen:
            kwargs[ key[plen+1:] ] = val

    # Import and make the object
    package = __import__('floof.model.filestore.' + pylons_config[prefix],
        globals(), locals(), ['FileStorage'], 0)
    return package.FileStorage(**kwargs)


# TODO: several steps here
# 3. add notion of file class for all filestorages; local can either ignore or use subdirectories
# fix this impl-per-module nonsense
class FileStorage(object):
    def put(self, key, fileobj):
        """Stores the data in the given fileobj under the given key."""
        raise NotImplementedError

    def url(self, key):
        """Returns a URL for accessing this file.
        
        Can be a fully-qualified URL, an absolute URL (starting with /) that
        will be taken relative to the app root, or None if the file cannot be
        found.
        """
        raise NotImplementedError
