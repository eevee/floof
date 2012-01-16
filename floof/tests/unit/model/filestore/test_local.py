import os
import shutil
import tempfile
import urllib2

import pytest
import transaction

from floof.model.filestore import get_storage_factory
from floof.tests import UnitTests
from floof.tests.unit.model.filestore import AlwaysFailDataManager
from floof.tests.unit.model.filestore import IntentionalError
from floof.tests.unit.model.filestore import storage_put, storage_put_tester


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
        super(TestLocalFileStore, self).tearDown()

    def _rmtree(self):
        # *nix bias, but good grief, we don't want to trip this accidentally
        assert '/tmp/' in self.directory, "Dare not call rmtree on chosen temp directory path '{0}'".format(self.directory)
        shutil.rmtree(self.directory)

    def _get_storage(self):
        settings = {
            'filestore': 'local',
            'filestore.directory': self.directory
        }
        storage = get_storage_factory(settings)()
        assert hasattr(storage, 'put')
        assert hasattr(storage, 'url')

        trxn = transaction.begin()
        trxn.join(storage)

        return storage

    def test_put(self):
        storage = self._get_storage()
        assert len(storage.stage) == 0
        storage_put_tester(storage)

    def test_url(self):
        storage = self._get_storage()
        cls, key, data = storage_put(storage)

        # URL should be available immediately
        url = storage.url(cls, key)
        assert url.startswith('file://')
        assert key in url

        transaction.commit()

        fetched = urllib2.urlopen(url, timeout=5)
        assert fetched.read() == data.read()

    def test_commit_process(self):
        storage = self._get_storage()
        cls, key, data = storage_put(storage)

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
        cls, key, data = storage_put(storage)
        assert not os.listdir(self.tempdir)

        # Simulate voting failure of another datamanager during commit
        transaction.get().join(AlwaysFailDataManager())
        with pytest.raises(IntentionalError):
            transaction.commit()

        # The tempfiles should have been cleaned up on failure
        assert os.path.exists(self.tempdir)
        assert not os.listdir(self.tempdir)
