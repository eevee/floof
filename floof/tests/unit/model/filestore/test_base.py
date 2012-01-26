import tempfile

import pytest

from floof.model.filestore import get_storage_factory
from floof.tests import UnitTests


class TestFilestorage(UnitTests):

    def test_get_factory(self):
        tempdir = tempfile.gettempdir()
        settings = {'filestore.directory': tempdir}
        with pytest.raises(ImportError):
            settings['filestore'] = 'floof.model.filestore.ocal.FileStorage'
            get_storage_factory(settings)
            settings['filestore'] = 'foo'
            get_storage_factory(settings)

        settings['filestore'] = 'floof.model.filestore.local.FileStorage'
        get_storage_factory(settings)
        settings['filestore'] = 'local'
        get_storage_factory(settings)
