from floof.tests import FunctionalTests

class TestMain(FunctionalTests):

    def test_index(self):
        """Test display of the front page."""
        response = self.app.get(self.url('root', my_thing='is_this'))
        assert 'floof' in response.body

    def test_log(self):
        """Test display of the public admin log page."""
        response = self.app.get(self.url('log'))
        assert 'Public Admin Log' in response
