from pyramid import testing

from floof.model import meta
from floof.tests import FunctionalTests
import floof.tests.sim as sim

class TestTags(FunctionalTests):

    def test_list(self):
        """Test display of tags index page."""
        response = self.app.get(self.url('tags.list'))
        # Test response...

    def test_artwork(self):
        """Test tagging an artwork."""
        # Create some art with a known tag
        user = sim.sim_user()
        artwork = sim.sim_artwork(user=user)
        tag = sim.sim_tag()
        artwork.tag_objs.append(tag)
        meta.Session.flush()

        # Ensure it shows in the tag's gallery
        res = self.app.get(self.url('tags.artwork', tag=tag))
        assert artwork.title in res
