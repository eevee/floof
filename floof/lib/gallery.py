# encoding: utf8
"""Shared gallery handling, including the wtforms form definition and a bunch
of easy SQL wrappers.

Intended to be used and usable from basically all over the place.  You probably
want the `GalleryView` class.
"""
from datetime import timedelta

from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_, case, or_
import wtforms.form, wtforms.fields

from floof import model

# TODO: tag filter; does this have a ticket?
# TODO: labels (is there a favorites ticket?)
# TODO: "art like this" on art page
# TODO: another special search, elsewhere, for friend-of-friends (watches of everyone in label x)

# TODO: Fixed things: any (viewable) userlabel, any (viewable) artlabel, friend-of-friend...?
class GalleryForm(wtforms.form.Form):
    """Form used all over the place for "searching" (really filtering) through
    art.
    """
    # TODO replace me with a special tag filter field that somehow interacts
    # correctly with the function below.  syntax should include:
    # - arbitrary boolean queries
    #   a | b?  a OR b?  OR(a b)??
    # - what to do with bogus syntax or nonexistent tags?
    # TODO this includes user searchin.  so what to do about uploader, if
    # anything?
    tags = wtforms.fields.TextField(u'Tags')
    # TODO maybe arbitrary-ish date search here?  center+radius.  I often find
    # I don't remember when something was made  :V
    time_radius = wtforms.fields.SelectField(u'Uploaded within',
        choices=[
            (u'all',    u'—'),
            (u'30m',    u'30 minutes'),
            (u'4h',     u'4 hours'),
            (u'24h',    u'24 hours'),
            (u'7d',     u'7 days'),
            (u'30d',    u'30 days'),
            (u'90d',    u'90 days'),
            (u'365d',   u'365 days'),
        ],
        default=u'all',
    )
    my_rating = wtforms.fields.SelectField(u'My rating',
        choices=[
            (u'all',    u'—'),
            (u'good',   u'Positive'),
            (u'ok',     u'Neutral'),
            (u'bad',    u'Negative'),
            # XXX other choices for users whose radius > 1?
            (u'any',    u'Any rating'),
            (u'none',   u'Not rated'),
        ],
        default=u'all',
    )
    # TODO: sort by similarity-to-artwork-x?
    sort = wtforms.fields.SelectField(u'Sort by',
        choices=[
            (u'uploaded_time',  u'time uploaded'),
            (u'rating',         u'rating (only shows the last 24h of art)'),
            # TODO implement me
            #(u'suggest',        u"how much I'd like it"),
        ],
        default=u'uploaded_time',
    )
    display = wtforms.fields.RadioField(u'Display',
        choices=[
            (u'thumbnails', u'Thumbnail grid'),
            (u'succinct',   u'Brief list'),
            (u'detailed',   u'Detailed list'),
        ],
        default=u'thumbnails',
    )

# Definitions of the time_radius options, expressed as timedelta params
TIME_RADII = {
    u'30m':    dict(minutes=30),
    u'4h':     dict(hours=4),
    u'24h':    dict(hours=24),
    u'7d':     dict(days=7),
    u'30d':    dict(days=30),
    u'90d':    dict(days=90),
    u'365d':   dict(days=365),
}


class GalleryView(object):
    """Represents a view of an art gallery.

    The definition of 'art gallery' is extremely subject to interpretation.  It
    may actually be the art owned by a single user, or it may be a tag or a
    label, or any combination thereof.  Who knows!  You can construct all of
    these using the filter methods.

    This class also handles roundtripping through HTTP forms; it can load
    filters from form data, and construct a query to reproduce all the filters
    applied so far.
    """
    def __init__(self, session=None, user=None):
        """Parameters:

        `session`
            The SQLAlchemy session to use.  If omitted, the current Pylons
            thread-local session will be used.
        `user`
            The currently-logged-in user, used for a handful of filters (e.g.
            filtering by "my" rating, or sorting in suggestion order).  May be
            omitted, in which case those filters will crash spectacularly.
        """
        if not session:
            session = model.meta.Session

        self.session = session
        self.user = user

        self.query = session.query(model.Artwork)
        self.order_clause = model.Artwork.uploaded_time.desc()


    ### Methods for building the query

    def filter_by_user(self, rel, user):
        """Filter the gallery by a user relationship: by/for/of.
        """
        self.query = self.query.filter(
            model.Artwork.user_artwork.any(
                relationship_type=rel,
                user_id=user.id,
            )
        )

    def filter_by_timedelta(self, delta):
        """Filter the gallery down to art uploaded no earlier than `delta`
        before now.
        """
        self.query = self.query.filter(
            model.Artwork.uploaded_time >= model.now() - delta)

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

            self.filter_by_user(relation, user)

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

    def filter_by_tag_query(self, tag_query):
        """Filter by an arbitrary Boolean set of tags.  The query itself is a
        string, which this method is responsible for parsing.

        Current syntax is just a space-delimited list of tags.
        """
        for tag in tag_query.split():
            try:
                self.filter_by_tag(tag)
            except NoResultFound:
                # XXX ???
                pass

    def filter_by_watches(self, user):
        """Filter the gallery down to only things `user` is watching."""
        # XXX make this work for multiple users
        self.query = self.query.filter(or_(
            # Check for by/for/of watching
            # XXX need an index on relationship_type, badly!
            model.Artwork.id.in_(
                self.session.query(model.UserArtwork.artwork_id)
                    .join((model.UserWatch, model.UserArtwork.user_id == model.UserWatch.other_user_id))
                    .filter(model.UserWatch.user_id == user.id)
                    .filter(case(
                        value=model.UserArtwork.relationship_type,
                        whens={
                            u'by': model.UserWatch.watch_by,
                            u'for': model.UserWatch.watch_for,
                            u'of': model.UserWatch.watch_of,
                        },
                    ))
            ),
            # Check for upload watching
            model.Artwork.uploader_user_id.in_(
                self.session.query(model.UserWatch.other_user_id)
                    .filter(model.UserWatch.user_id == user.id)
                    .filter(model.UserWatch.watch_upload == True)  # gross
            ),
        ))

    def filter_by_label(self, label):
        """Filter the gallery down to a particular label.  Note that labels are
        user-specific, so this usually only makes sense when browsing a
        specific user's art.
        """
        raise NotImplementedError


    def order_by(self, order):
        """Changes the sort order.  May be one of "uploaded_time", "rating".

        The default is "uploaded_time".
        """
        if order == 'uploaded_time':
            self.order_clause = model.Artwork.uploaded_time.desc()
        elif order == 'rating':
            self.order_clause = model.Artwork.rating_score.desc()
        else:
            raise ValueError("No such ordering {0}".format(order))

    ### Methods for reading form data

    def read_form_data(self, formdata):
        """Feeds the given `formdata` into a wtforms form and applies the
        appropriate filters.

        Returns the result of `form.validate()`.  If the form isn't valid, no
        filtering is done.
        """
        # TODO auto-shorten; oh no how would this even work
        # TODO do nothing if formdata is blank??
        form = GalleryForm(formdata)
        # XXX this is lame.
        self.form = form
        if not form.validate():
            # XXX should this raise an exception instead???
            return False

        if form.tags.data:
            self.filter_by_tag_query(form.tags.data)

        # TODO: allow "popular per day" a la e621?
        # TODO: or for "popular recently", use popularity * age for falloff?
        if form.time_radius.data != u'all':
            self.filter_by_timedelta(
                timedelta(**TIME_RADII[form.time_radius.data]))

        # TODO: only show this field at all when user exists
        if form.my_rating.data != u'all' and self.user:
            # This is done here instead of via a method until someone comes up
            # with a decent method interface.
            rating_spec = form.my_rating.data
            my_rating_subq = self.session.query(model.ArtworkRating) \
                .filter_by(user=self.user) \
                .subquery()

            if rating_spec == u'none':
                # Filtering by NO rating is a little different.  Need to
                # left-join to my ratings and filter on NULLs
                self.query = self.query \
                    .outerjoin((my_rating_subq,
                        model.Artwork.id == my_rating_subq.c.artwork_id)) \
                    .filter(my_rating_subq.c.artwork_id == None)

            else:
                # Otherwise, regular-join to my ratings
                self.query = self.query \
                    .join((my_rating_subq,
                        model.Artwork.id == my_rating_subq.c.artwork_id))

                if rating_spec == u'good':
                    self.query = self.query.filter(
                        my_rating_subq.c.rating > 0.0)
                elif rating_spec == u'ok':
                    self.query = self.query.filter(
                        my_rating_subq.c.rating == 0.0)
                elif rating_spec == u'bad':
                    self.query = self.query.filter(
                        my_rating_subq.c.rating < 0.0)
                # Only other option is 'any', which is taken care of by the
                # join alone

        self.order_by(form.sort.data)
        # TODO: rating sort should force last 24h or less
        # TODO: suggestion sort???

        return True


    ### Methods for examining the result

    def get_form(self):
        """Builds and returns a wtforms `Form` representing the current state
        of the view.  Loading this form's data into a new `GalleryView` should
        produce exactly the same search.
        """
        raise NotImplementedError

    def get_query(self):
        """Get the constructed query, sorted in the usual way: by uploaded
        time, most recent first.
        """
        return self.query.order_by(self.order_clause)
