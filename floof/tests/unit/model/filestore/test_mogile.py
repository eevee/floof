import urllib2

import pytest
import transaction

from floof.model.filestore import get_storage_factory
from floof.tests import UnitTests
from floof.tests.unit.model.filestore import AlwaysFailDataManager
from floof.tests.unit.model.filestore import IntentionalError
from floof.tests.unit.model.filestore import storage_put, storage_put_tester


@pytest.mark.skipif("sys.platform == 'win32'")
class TestMogileFileStore(UnitTests):

    def setUp(self):
        super(TestMogileFileStore, self).setUp()

        reqattrs = ('filestore.trackers', 'filestore.domain')
        for attr in reqattrs:
            if attr not in self.config.registry.settings:
                pytest.skip('MogileFS FileStorage tests require the following '
                            'configuration attributes to run: {0}'
                            .format(reqattrs))

    def _get_storage(self):
        settings = self.config.registry.settings
        storage = get_storage_factory(settings)()
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

        # URL should not be available immediately
        assert not storage.url(cls, key)

        transaction.commit()

        # ... but must be available after commit
        url = storage.url(cls, key)
        fetched = urllib2.urlopen(url, timeout=5)
        assert fetched.read() == data.read()

    def test_other_dm_fail(self):
        storage = self._get_storage()
        cls, key, data = storage_put(storage)
        assert not storage.url(cls, key)

        # Simulate voting failure of another datamanager during commit
        transaction.get().join(AlwaysFailDataManager())
        with pytest.raises(IntentionalError):
            transaction.commit()

        # The tempfiles should have been cleaned up on failure
        assert not storage.url(cls, key)
