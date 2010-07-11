from floof.tests import *

class TestArtController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='art', action='index'))
        # Test response...
