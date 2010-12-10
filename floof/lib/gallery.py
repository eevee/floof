"""Shared gallery handling.

Intended to be used and usable from basically all over the place.  You probably
want the `GalleryView` class.
"""
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound

from floof import model

class GalleryView(object):
    """Represents a view of an art gallery.

    The definition of 'art gallery' is extremely subject to interpretation.  It
    may actually be the art owned by a single user, or it may be a tag or a
    label, or any combination thereof.  Who knows!
    """
    def __init__(self, session=None):
        """Attempts"""
        if not session:
            session = model.meta.Session

        self.session = session
        self.query = session.query(model.Artwork)


    ### Methods for building the query
    def filter_by_tag(self, tag):
        """Filter the gallery by a named tag.  It may be a regular tag 'foo',
        or a special tag like 'by:foo'.
        """
        if ' ' in tag:
            raise ValueError("Tags cannot contain spaces; is this a list of tags?")

        if tag.startswith(('by:', 'for:', 'of:')):
            # Special user tag
            relation, _, username = tag.partition(':')
            try:
                user = self.session.query(model.User).filter_by(name=username).one()
            except NoResultFound:
                # XXX Do something better??
                raise

            self.query = self.query.filter(
                model.Artwork.user_artwork.any(
                    relationship_type=relation,
                    user_id=user.id,
                )
            )

        else:
            # Regular tag
            try:
                tag = self.session.query(model.Tag).filter_by(name=tag).one()
            except NoResultFound:
                # XXX
                raise

            self.query = self.query.filter(
                model.Artwork.tag_objs.any(id=tag.id)
            )


    ### Methods for examining the result
