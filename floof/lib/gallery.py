# encoding: utf8
"""Shared gallery handling, including the wtforms form definition and a bunch
of easy SQL wrappers.

Intended to be used and usable from basically all over the place.  You probably
want the `GallerySieve` class.
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
    # TODO paging!
    # - when sorting by date, do this by "skipping" to a certain date, to avoid
    #   problems with LIMIT...OFFSET
    # - otherwise, you'll need to actually use LIMIT and do pages as normal.
    #   boo.
    # - when doing date skipping, perhaps instead of jumping back by 2/3/4
    #   pages, offer to skip back by increasing chunks of time?  and/or allow
    #   just outright typing in a custom place to jump to
    # - when doing date skipping, does jumping backwards need to be a concern,
    #   or can we just rely on the back button?
    # TODO counts of results?  blech.  if nothing else, select one more than
    #   necessary, and only show a "next" button if it's useful.
    # TODO handle no results
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


bogus_form_data = object()

class DuplicateFilterError(Exception): pass

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

    def __init__(self, session=None, user=None, formdata=None):
        """Parameters:

        `session`
            The SQLAlchemy session to use.  If omitted, the current Pylons
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
        """
        if not session:
            session = model.meta.Session

        self.session = session
        self.user = user

        self._query = session.query(model.Artwork)
        self._form = GalleryForm(formdata)
        self.order_clause = model.Artwork.uploaded_time.desc()

        self.use_form = formdata is not None
        if formdata:
            if self._form.validate():
                self._apply_formdata()

    def _apply_formdata(self):
        # TODO auto-shorten?  oh no how would this even work
        form = self._form

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
                self._query = self._query \
                    .outerjoin((my_rating_subq,
                        model.Artwork.id == my_rating_subq.c.artwork_id)) \
                    .filter(my_rating_subq.c.artwork_id == None)

            else:
                # Otherwise, regular-join to my ratings
                self._query = self._query \
                    .join((my_rating_subq,
                        model.Artwork.id == my_rating_subq.c.artwork_id))

                if rating_spec == u'good':
                    self._query = self._query.filter(
                        my_rating_subq.c.rating > 0.0)
                elif rating_spec == u'ok':
                    self._query = self._query.filter(
                        my_rating_subq.c.rating == 0.0)
                elif rating_spec == u'bad':
                    self._query = self._query.filter(
                        my_rating_subq.c.rating < 0.0)
                # Only other option is 'any', which is taken care of by the
                # join alone

        self.order_by(form.sort.data)
        # TODO: rating sort should force last 24h or less
        # TODO: suggestion sort???


    ### Independent filter methods

    def filter_by_timedelta(self, delta):
        """Find art uploaded no earlier than `delta` before now.

        Must be one of the values allowed in the form, above, and so is not
        really suited for purely from-code use.
        """
        self._query = self._query.filter(
            model.Artwork.uploaded_time >= model.now() - delta)

    ### Tag filter methods

    def filter_by_user(self, rel, user):
        """Filter the gallery by a user relationship: by/for/of.
        """
        self._query = self._query.filter(
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

        try:
            tag = self.session.query(model.Tag).filter_by(name=tag).one()
        except NoResultFound:
            # XXX
            raise

        self._query = self._query.filter(
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
                    user = self.session.query(model.User).filter_by(username=username).one()
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
        self._query = self._query.filter(or_(
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


    ### The fruits of our labors

    @property
    def wtform(self):
        """A wtforms `Form` representing the current state of the view.
        Loading this form's data into a new `GallerySieve` should produce
        exactly the same search.
        """
        if self._form:
            # Already got the form from read_form_data
            return self._form

        # XXX implement this asap
        return GalleryForm()

    @property
    def sqla_query(self):
        """The constructed SQLAlchemy query."""
        print self._query
        return self._query.order_by(self.order_clause)

    def get_query(self): return self.sqla_query
