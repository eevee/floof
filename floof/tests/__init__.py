"""floof test package

This module provides sub-classes of unittest.TestCase that are provided with
and manage an in-memory SQLite database, populated with the default entries
from floof.lib.setup.

A transaction is begun before each request and aborted immediately following.

Designed to be run with py.test

"""
import os.path
import transaction
import unittest
import webtest

import pytest

from paste.deploy import appconfig
from pyramid import testing
from pyramid.paster import get_app
from pyramid.url import URLMethodsMixin
from sqlalchemy import create_engine
from zope.sqlalchemy import ZopeTransactionExtension

from floof.lib.setup import populate_db
import floof.model
from floof.routing import configure_routing

__all__ = ['FunctionalTests', 'UnitTests']

def _prepare_env():
    """Configure the floof model and set up a database the default entries."""
    floof.model.session.remove()
    floof.model.initialize(
        create_engine('sqlite://'),
        extension=ZopeTransactionExtension())

    transaction.begin()
    populate_db(floof.model.TableBase.metadata, floof.model.session,
        is_test=True)
    transaction.commit()

# XXX: major import side-effects ahoy!
_prepare_env()


def test_get_settings():
    # Get paster to interpret the passed config ini-spec
    conffile = getattr(pytest.config.option, 'config', None)
    if conffile is None:
        return None

    ini_spec = os.path.abspath(conffile)
    settings = appconfig('config:' + ini_spec)
    return settings


class UnitTests(unittest.TestCase):
    """Brings up a lightweight db and threadlocal environment."""

    def setUp(self):
        # Initialize a db session and a threadlocal environment
        transaction.begin()
        self.session = floof.model.session()
        # The config will be picked up automatically by Pyramid as a thread
        # local
        self.config = testing.setUp(settings=test_get_settings())

    def tearDown(self):
        # Roll back everything and discard the threadlocal environment
        testing.tearDown()
        transaction.abort()


class FunctionalTests(UnitTests):
    """Brings up the full Pyramid app."""

    def setUp(self):
        super(FunctionalTests, self).setUp()

        # HACK: Get Route / URL Dispatch name-to-path lookups working by using
        # a BS request object
        # NOTE: Will blow up on routes with pregenrators that inspect request
        class FakeRequest(URLMethodsMixin):
            script_name = ''

        configure_routing(self.config)
        self._fake_request = FakeRequest()
        self.url = self._fake_request.route_path

    def __init__(self, *args, **kwargs):
        # FIXME: Hardcoded!
        wsgiapp = get_app('paster.ini', 'floof-test')
        self.app = webtest.TestApp(wsgiapp)

        super(FunctionalTests, self).__init__(*args, **kwargs)
