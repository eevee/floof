from floof.tests import *

class TestMainController(TestController):

    def test_index(self):
        """Test that the front page loads."""
        response = self.app.get(url(controller='main', action='index'))
        # Test response...

    def test_log(self):
        """Test that the public admin log page loads."""
        response = self.app.get(url(controller='main', action='log'))
        assert 'Public Admin Log' in response

