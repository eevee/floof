from floof.tests import *
import floof.tests.sim as sim

from floof.model import meta

class TestTagsController(TestController):

    def test_index(self):
        """Test display of tags index page."""
        response = self.app.get(url(controller='tags', action='index'))
        # Test response...

    def test_artwork(self):
        """Test tagging an artwork."""
        # Create some art with a known tag
        user = sim.sim_user()
        artwork = sim.sim_artwork(user=user)
        tag = sim.sim_tag()
        artwork.tag_objs.append(tag)
        meta.Session.commit()

        # Ensure it shows in the tag's gallery
        res = self.app.get(url(controller='tags', action='artwork', name=tag.name))
        assert artwork in res.tmpl_context.gallery_view.get_query()
