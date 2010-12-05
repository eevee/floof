from floof.tests import *

class TestControlsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='controls', action='index'))
        # Test response...
