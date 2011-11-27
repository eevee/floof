# encoding: utf8
"""Shared gallery handling, including the wtforms form definition and a bunch
of easy SQL wrappers.

Intended to be used and usable from basically all over the place.  You probably
want the `GallerySieve` class.
"""
from datetime import timedelta

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import case, or_
import wtforms.form, wtforms.fields

from floof.lib import pager
from floof import model

# TODO: labels (is there a favorites ticket?)
# TODO: "art like this" on art page
# TODO: another special search, elsewhere, for friend-of-friends (watches of everyone in label x)

class GalleryForm(wtforms.form.Form):
    """Form used all over the place for "searching" (really filtering) through
    art.
    """
    # TODO replace me with a special tag filter field that somehow interacts
    # correctly with the function below.  syntax should include:
    # - arbitrary boolean queries
    #   a | b?  a OR b?  OR(a b)??
    # - then bogus tags can just error back to the form, if that makes sense.
    #   or just show nothing, with a warning.  not sure which is less useful.
    # TODO this includes user searchin.  so what to do about uploader, if
    # anything?
    tags = wtforms.fields.TextField(u'Tags')
    # TODO maybe arbitrary-ish date search here?  center+radius.  I often find
    # myself wanting to look for stuff that's "about six months old"
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
    sort = wtforms.fields.SelectField(u'Sort by',
        choices=[
            (u'uploaded_time',  u'time uploaded'),
            (u'rating',         u'rating (restricted to the last 24h)'),
            (u'rating_count',   u'number of ratings'),
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


PAGE_SIZE = 64  # XXX

class GallerySieve(object):
    """Handles filtering art by various criteria.  Different places within the
    site show different chunks of artwork, but ought to function similarly;
    this class is the common interface and coordinates rendering, database
    access, and HTTP forms for user-specified filters.

    The usual workflow is to apply some of the `filter_*` methods, then feed
    this object to the `render_gallery` def in art/lib.mako.  The user can then
    apply some further standard filtering to the art and submit back to the
    same page.

    Most filter methods aren't intended to be called multiple times.  So don't
    do that.  One explicit exception is that all the tag-related filters can be
    combined arbitrarily; they'll be ANDed together.
    """

    default_order_clause = model.Artwork.uploaded_time.desc()
    temporal_column_name = 'uploaded_time'

    def __init__(self, session=None, user=None, formdata=None, countable=False):
        """Parameters:

        `session`
            The SQLAlchemy session to use.  If omitted, the current Pyramid
            thread-local session will be used.
        `user`
            The currently-logged-in user, used for a handful of filters (e.g.
            filtering by "my" rating, or sorting in suggestion order).  May be
            omitted, in which case those filters will crash spectacularly.
            If provided, this user's default filter set will automatically be
            applied.
        `formdata`
            Form data.  If provided, it'll be loaded into the wtforms object
            and appropriate filters will be applied.  If this is omitted
            entirely, the rendered gallery won't have a filter form at all.
        `countable`
            If set to True, the gallery display will include a count of the
            total number of items (even when filtered!), and the page list will
            run from first to last.  If set to False (the default), the page
            list will instead trail off after the current page, only showing a
            next page link if there are more items to see.  The intention is
            that this be set to True only for "real" gallery, such as the
            artwork a single user owns.
        """
        if not session:
            session = model.session

        self.session = session
        self.user = user
        self.countable = countable
        self.display_mode = 'thumbnails'

        self.query = session.query(model.Artwork) \
            .order_by(self.default_order_clause)

        self.form = GalleryForm(formdata)
        self.original_formdata = formdata or {}
        if formdata:
            if self.form.validate():
                self._apply_formdata()

    def _apply_formdata(self):
        # TODO auto-shorten?  oh no how would this even work
        form = self.form

        self.display_mode = form.display.data

        if form.tags.data:
            self.filter_by_tag_query(form.tags.data)

        # TODO: allow "popular per day" a la e621?
        # TODO: or for "popular recently", use popularity * age for falloff?
        if form.time_radius.data != u'all':
            self.filter_by_recency(
                timedelta(**TIME_RADII[form.time_radius.data]))

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
        if form.sort.data == u'rating':
            # Only allow the past 24 hours when sorting by absolute rating
            self.filter_by_recency(timedelta(hours=24))


    ### Independent filter methods

    def filter_by_age(self, dt):
        """Find art uploaded at or before `dt`."""
        self.query = self.query.filter(model.Artwork.uploaded_time <= dt)

    def filter_by_recency(self, delta):
        """Find art uploaded no earlier than `delta` before now."""
        self.query = self.query.filter(
            model.Artwork.uploaded_time >= model.now() - delta)

    ### Tag filter methods

    def filter_by_user(self, rel, user):
        """Filter the gallery by a user relationship: by/for/of.
        """
        self.query = self.query.filter(
            model.Artwork.user_artwork.any(
                relationship_type=rel,
                user_id=user.id,
            )
        )

    def filter_by_tag(self, tag):
        """Filter the gallery by a named tag.  Special tags (e.g., by:foo) are
        not allowed.
        """
        if ' ' in tag:
            raise ValueError("Tags cannot contain spaces; is this a list of tags?")
        if tag.startswith(('by:', 'for:', 'of:')):
            raise ValueError("Cannot filter by special tags; use filter_by_user instead")

        # This will raise NoResultFound with a bogus tag -- as it should, since
        # this is called from our code, not directly on user input
        tag = self.session.query(model.Tag).filter_by(name=tag).one()

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
                if u':' in tag:
                    rel, _, username = tag.partition(':')
                    user = self.session.query(model.User).filter_by(name=username).one()
                    self.filter_by_user(rel, user)
                else:
                    self.filter_by_tag(tag)
            except NoResultFound:
                # XXX ???
                pass

    ### Special filter methods; only one of these can exist in a form at a time

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
        """Changes the sort order.  May be one of "uploaded_time", "rating",
        "rating_count".

        The default is "uploaded_time".
        """
        self.temporal_column_name = None

        if order == 'uploaded_time':
            order_column = model.Artwork.uploaded_time
            self.temporal_column_name = 'uploaded_time'
        elif order == 'rating':
            order_column = model.Artwork.rating_score
        elif order == 'rating_count':
            order_column = model.Artwork.rating_count
        else:
            raise ValueError("No such ordering {0}".format(order))

        self.query = self.query.order_by(None) \
            .order_by(order_column.desc(), self.default_order_clause)


    ### The fruits of our labors

    def evaluate(self):
        """Executes the query.  Returns a pager object.

        A word on how the paging works:
        - If the sieve is created with countable=True, you'll get a regular
          numeric pager, regardless of anything else.
        - If the sieve is created with countable=False, you'll get a numeric
          pager that trails off at the end.
        - If the sieve is created with countable=False AND is sorted by time
          AND the user has gone back "too far", the "next" link will switch to
          time-based paging instead.
        """
        common_kw = dict(
            query=self.query,
            page_size=PAGE_SIZE,
            formdata=self.original_formdata,
        )

        if self.countable:
            return pager.DiscretePager(
                countable=True,
                **common_kw
            )
        else:
            # Only use temporal paging if we actually can, AND if the formdata
            # has a timeskip key already
            if self.temporal_column_name and \
                'timeskip' in self.original_formdata:

                return pager.TemporalPager(
                    column_name='uploaded_time',
                    **common_kw
                )

            return pager.DiscretePager(
                countable=False,
                **common_kw
            )
