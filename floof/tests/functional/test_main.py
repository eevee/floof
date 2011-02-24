from floof.tests import *

class TestMainController(TestController):

    def test_index(self):
        """Test display of the front page."""
        response = self.app.get(url(controller='main', action='index'))
        # Test response...

    def test_log(self):
        """Test display of the public admin log page."""
        response = self.app.get(url(controller='main', action='log'))
        assert 'Public Admin Log' in response

    def test_cookies_disabled(self):
        """Test display of the "cookies disabled" error page."""
        response = self.app.get(url(controller='main', action='cookies_disabled'))
        assert 'Cookies Disabled' in response
