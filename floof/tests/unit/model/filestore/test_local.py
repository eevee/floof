import cStringIO
import os
import shutil
import string
import tempfile
import urllib2
import random

import pytest
import transaction

from floof.model.filestore import get_storage_factory
from floof.tests import UnitTests


class IntentionalError(Exception): pass


class AlwaysFailDataManager(object):
    def abort(self, transaction): pass
    def tpc_begin(self, transaction): pass
    def commit(self, transaction): pass
    def tpc_finish(self, transaction): pass
    def tpc_abort(self, transaction): pass

    def tpc_vote(self, transaction):
        raise IntentionalError

    def sortKey(self):
        return '~~~~hopefullyLast'


class TestLocalFileStore(UnitTests):

    def setUp(self):
        super(TestLocalFileStore, self).setUp()

        tempdir = tempfile.gettempdir()
        self.directory = os.path.join(tempdir, 'pytestfloof')
        self.tempdir = os.path.join(self.directory, '__temp__')
        if os.path.exists(self.directory):
            self._rmtree()
        os.mkdir(self.directory)

    def tearDown(self):
        self._rmtree()

    def _rmtree(self):
        assert '/tmp/' in self.directory, "Dare not call rmtree on chosen temp directory path '{0}'".format(self.directory)
        shutil.rmtree(self.directory)

    def _make_key(self):
        return u''.join((random.choice(string.hexdigits) for i in xrange(10)))

    def _get_storage(self):
        settings = {
            'filestore': 'local',
            'filestore.directory': self.directory
        }
        storage = get_storage_factory(settings)()
        trxn = transaction.begin()
        trxn.join(storage)

        return storage

    def _put(self, storage, data=None):
        if data is None:
            length = random.choice(range(10, 1000))
            data = ''.join((random.choice(string.printable)
                            for i in xrange(length)))

        data = cStringIO.StringIO(data)
        key = self._make_key()
        storage.put('class', key, data)
        data.seek(0)

        return 'class', key, data

    def test_get_factory(self):
        settings = {'filestore.directory': self.directory}
        with pytest.raises(ImportError):
            settings['filestore'] = 'floof.model.filestore.ocal.FileStorage'
            get_storage_factory(settings)
            settings['filestore'] = 'foo'
            get_storage_factory(settings)

        settings['filestore'] = 'floof.model.filestore.local.FileStorage'
        get_storage_factory(settings)
        settings['filestore'] = 'local'
        storage_factory = get_storage_factory(settings)

        storage = storage_factory()
        assert hasattr(storage, 'put')
        assert hasattr(storage, 'url')

    def test_put(self):
        storage = self._get_storage()

        assert len(storage.stage) == 0
        cls, key, data = self._put(storage)

        # Check that something got inserted into storage.stage
        assert len(storage.stage) == 1
        idx = storage._idx(cls, key)
        assert cls in idx
        assert key in idx
        assert idx in storage.stage

        # Check the values of the tuple inserted into storage.stage
        entry = storage.stage[idx]
        assert len(entry) == 3
        c, k, d = entry
        assert c == cls
        assert k == key
        d.seek(0)
        data.seek(0)
        assert d.read() == data.read()

    def test_url(self):
        storage = self._get_storage()
        cls, key, data = self._put(storage)

        # URL should be available immediately
        url = storage.url(cls, key)
        assert url.startswith('file://')
        assert key in url

        transaction.commit()

        fetched = urllib2.urlopen(url, timeout=5)
        assert fetched.read() == data.read()

    def test_commit_process(self):
        storage = self._get_storage()
        cls, key, data = self._put(storage)

        trxn = transaction.get()
        storage.tpc_begin(trxn)
        storage.commit(trxn)
        storage.tpc_vote(trxn)

        stagecopy = [(c, k) for c, k, d in storage.stage.itervalues()]
        temppaths = storage.tempfiles.values()

        # At this stage, the new files should be written out to the temp dir
        for temppath in temppaths:
            assert os.path.isfile(temppath)

        storage.tpc_finish(trxn)

        # Now the new files should have moved from their temp dir...
        for temppath in temppaths:
            assert not os.path.exists(temppath)

        # To their final locations
        for cls, key in stagecopy:
            assert os.path.isfile(storage._path(self.directory, cls, key))

    def test_other_dm_fail(self):
        storage = self._get_storage()
        cls, key, data = self._put(storage)
        assert not os.listdir(self.tempdir)

        # Simulate voting failure of another datamanager during commit
        transaction.get().join(AlwaysFailDataManager())
        with pytest.raises(IntentionalError):
            transaction.commit()

        # The tempfiles should have been cleaned up on failure
        assert os.path.exists(self.tempdir)
        assert not os.listdir(self.tempdir)
