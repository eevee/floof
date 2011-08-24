"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.
"""
from unittest import TestCase

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand
###from pylons import url
from routes.util import URLGenerator
from webtest import TestApp

###import pylons.test

from floof.model import meta

__all__ = ['environ', 'url', 'TestController']

# Invoke websetup with the current config file
SetupCommand('setup-app').run([pylons.test.pylonsapp.config['__file__']])

environ = {}

class TestController(TestCase):

    def setUp(self):
        # See: http://www.sqlalchemy.org/docs/orm/session.html#joining-a-session-into-an-external-transaction
        # This will allow app code to commit() and otherwise use the session as
        # normal, but undoes everything between individual tests
        # Ditch any existing session first
        meta.Session.remove()
        # Create a non-ORM transaction, which tricks ORM .commit() into not
        # actually committing
        conn = meta.engine.connect()
        self._transaction = conn.begin()
        meta.Session.configure(bind=conn)

    def tearDown(self):
        # Roll back everything, discard the session, and un-reconfigure it
        self._transaction.rollback()
        meta.Session.remove()
        meta.Session.configure(bind=meta.engine)

    def __init__(self, *args, **kwargs):
        if pylons.test.pylonsapp:
            wsgiapp = pylons.test.pylonsapp
        else:
            wsgiapp = loadapp('config:%s' % config['__file__'])
        config = wsgiapp.config
        self.app = TestApp(wsgiapp)
        url._push_object(URLGenerator(config['routes.map'], environ))
        TestCase.__init__(self, *args, **kwargs)
