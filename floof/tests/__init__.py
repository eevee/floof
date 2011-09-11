"""floof test package

This module provides sub-classes of unittest.TestCase that are provided with
and manage an in-memory SQLite database, populated with the default entries
from floof.lib.setup.

A transaction is begun before each request and aborted immediately following.

Designed to be run with py.test
"""
import functools
import transaction
import unittest
import webtest

from pyramid import testing
from pyramid.paster import get_app
from pyramid.url import route_path
from sqlalchemy import create_engine
from zope.sqlalchemy import ZopeTransactionExtension

from floof.lib.setup import populate_db
from floof.model import initialize
from floof.model import meta
from floof.routing import configure_routing

__all__ = ['FunctionalTests', 'UnitTests']

def _prepare_env():
    """Configure the floof model and set up a database the default entries."""
    meta.Session.remove()
    engine = create_engine('sqlite://')
    initialize(engine)
    meta.Session.configure(bind=meta.engine, extension=ZopeTransactionExtension())

    transaction.begin()
    populate_db(meta, is_test=True)
    transaction.commit()

# XXX: major import side-effects ahoy!
_prepare_env()

class UnitTests(unittest.TestCase):
    """Brings up a lightweight db and threadlocal environment."""

    def setUp(self):
        # Initialize a db session and a threadlocal environment
        transaction.begin()
        self.session = meta.Session()
        # The config will be picked up automatically by Pyramid as a thread
        # local
        self.config = testing.setUp()

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
        class BS:
            script_name = ''

        configure_routing(self.config)
        self.url = functools.partial(route_path, request=BS())

    def __init__(self, *args, **kwargs):
        # FIXME: Hardcoded!
        wsgiapp = get_app('paster.ini', 'floof-test')
        self.app = webtest.TestApp(wsgiapp)

        super(FunctionalTests, self).__init__(*args, **kwargs)
