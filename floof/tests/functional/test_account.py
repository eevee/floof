from floof.tests import *

class TestAccountController(TestController):

    def test_login(self):
        response = self.app.get(url(controller='account', action='login'))
        # Test response...
