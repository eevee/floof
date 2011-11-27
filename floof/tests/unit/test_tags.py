"""
This file doesn't perform any worthwhile tests ("yep, it exists" tests make
more sense in a functional test suite) it's just an example of how one might
construct a unit test.  Unit tests will likely be most useful run against libs.
"""
import string
import random

from pyramid import testing

from floof.model import Tag
from floof.tests import UnitTests

class TestTagViews(UnitTests):

    def _make_tag(self, name=None):
        if name is None:
            name = u''.join((random.choice(string.letters) for i in xrange(10)))
        tag = Tag(name)
        self.session.add(tag)
        self.session.flush()
        return tag

    def test_index(self):
        """Test that the tag view page exists."""
        from floof.views.tags import index

        request = testing.DummyRequest()
        tag = self._make_tag()

        render_dict = index(None, request)

        # ['tags'] is a query on the Tag table
        q = render_dict['tags'].filter_by(name=tag.name)

        assert q.one().name == tag.name

    def test_view(self):
        """Test that the tag view page exists."""
        from floof.views.tags import view

        request = testing.DummyRequest()
        tag = self._make_tag()

        render_dict = view(tag, request)

        assert render_dict['tag'].name == tag.name

    def test_artwork(self):
        """Test that the tag artwork filter page exists."""
        from floof.views.tags import artwork
        from floof.model import AnonymousUser

        request = testing.DummyRequest()
        request.user = AnonymousUser()
        request.params = None
        tag = self._make_tag()

        render_dict = artwork(tag, request)

        assert render_dict['tag'].name == tag.name
