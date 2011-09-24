"""Classes for dividing a number of items into pages and showing controls for
navigating between such.
"""
from __future__ import division

from calendar import timegm
from collections import namedtuple
from datetime import datetime
import math

import pytz

def _datetime_to_query(dt):
    """Converts a datetime to some arbitrary and unspecified format appropriate
    for putting in a query and round-tripping.

    This format happens to be a UTC Unix timestamp with fractional seconds.
    The returned value is a string, to avoid stupid float weirdness.
    """
    timestamp = timegm(dt.timetuple())
    return u"{whole}.{part:06d}".format(
        whole=timestamp,
        part=dt.microsecond,
    )

def _datetime_from_query(ts):
    """Converts the above arbitrary format back to a datetime object, complete
    with a time zone.  `ts` should be a string, straight out of the query.

    Returns None if `ts` is missing or junk.
    """
    if not ts:
        return None

    # Avoid using float() on the way back in, too
    if u'.' in ts:
        seconds, microseconds = ts.split('.', 1)
        # Pad to six digits
        microseconds = (microseconds + u'000000')[0:6]
    else:
        seconds = ts
        microseconds = 0

    try:
        dt = datetime.fromtimestamp(int(seconds), pytz.utc)
        dt = dt.replace(microsecond=int(microseconds))
        return dt
    except TypeError:
        # Nothing reasonable to do, since this is supposed to be a value just
        # for us.  If someone has been dicking with it...  ignore it
        return None


class DiscretePager(object):
    """Handles navigation between pages of query objects.  Rendering is done by
    `discrete_page` in lib.mako.
    """
    pager_type = 'discrete'
    maximum_skip = 1000

    def __init__(self, query, page_size, formdata={}, radius=3, countable=False):
        """Create a pager.  The current page is taken from 'skip' in the given
        `formdata`.

        `query` is assumed to be a SQLAlchemy query object, without any limits
        applied; this class will do the limiting based on `formdata['skip']`.

        `radius` is the number of page numbers to show around the current page.

        `countable` is for DoS prevention, as follows.
        - When set to True, the total number of items in the query will be
          counted, and the resulting page list will include numbering to the
          last page.
        - When set to False, the query will not be counted, and the page list
          will only show the following page number (if appropriate) and an
          ellipsis.  Additionally, no OFFSET greater than this object's
          `maximum_skip` will ever be allowed.
        """
        self.formdata = formdata.copy()
        self.formdata.pop('timeskip', None)  # get rid of cruft, just in case

        self.page_size = page_size
        self.radius = radius

        try:
            self.skip = int(self.formdata.pop('skip'))
        except (KeyError, ValueError, TypeError):
            self.skip = 0
        if self.skip < 0:
            # XXX or 404?
            self.skip = 0

        self.countable = countable
        if self.countable:
            self.item_count = query.count()
            self.last_page = int(math.ceil(
                self.item_count / self.page_size - 1))

            self.skip = min(self.skip, self.item_count)
        else:
            self.item_count = None
            self.last_page = None

            self.skip = min(self.skip, self.maximum_skip)

        self.current_page = self.skip / page_size

        # Get one extra, for figuring out where the next page starts, and
        # whether one exists
        self.items = query.limit(page_size + 1).offset(self.skip).all()
        self.visible_count = len(self.items)
        self.next_item = None
        if len(self.items) > page_size:
            self.next_item = self.items.pop()

    def __iter__(self):
        return iter(self.items)

    def pages(self):
        """Yields a list of page numbers, or None to indicate chunks of skipped
        pages.

        Page numbers are indexed at 0.  You may want to bump them by 1 for
        display.
        """
        # The page list comes in three sections.  Given radius=3:
        # 0 1 2 ... n-2 n-1 n n+1 n+2 ... m-2 m-1 m
        # Alas, some caveats:
        # - These sections might overlap.
        # - The current page might not be integral.
        delta = self.radius - 1  # since the below two are off by one
        before_current = int(math.ceil(self.current_page - 1))
        after_current = int(math.floor(self.current_page + 1))
        pages = []

        # First through current
        if before_current - delta <= 1:
            pages.extend(range(0, before_current + 1))
        else:
            pages.append(None)
            pages.extend(range(
                before_current - delta, before_current + 1))

        # Current
        pages.append(self.current_page)

        # Current through end
        if self.last_page is None:
            # Don't know the last page.  Show one more and ..., if appropriate
            if self.next_item and \
                after_current * self.page_size <= self.maximum_skip:

                pages.append(after_current)
                pages.append(None)
            return pages

        if after_current + delta >= self.last_page - 1:
            pages.extend(range(
                after_current, self.last_page + 1))
        else:
            pages.extend(range(after_current, after_current + delta + 1))
            pages.append(None)

        return pages

    def formdata_for(self, skip):
        """Returns the provided `formdata`, with its 'skip' key updated to the
        provided value.
        """
        formdata = self.formdata.copy()
        # skip=0 doesn't get put in the query
        if skip:
            formdata['skip'] = int(round(skip))
        return formdata

    def formdata_for_temporal(self, column_name):
        """Returns the provided `formdata`, with a 'timeskip' key for the first
        item on the following page.  Used by `GallerySieve` for switching to
        temporal paging after so many results.
        """
        formdata = self.formdata.copy()
        formdata['timeskip'] = _datetime_to_query(
            getattr(self.next_item, column_name))
        return formdata

    @property
    def is_last_page(self):
        return self.next_item is None

    @property
    def is_last_allowable_page(self):
        """Returns True if this is an uncountable pager and there would be more
        pages, but we won't let you see them.
        """
        if self.countable:
            return False
        if self.is_last_page:
            return False

        # If we have 10-item pages, the max limit is 40, and we've skipped 38,
        # it's still okay to see the next (integral) page
        if int(self.current_page + 1) * self.page_size > self.maximum_skip:
            return True

        return False


class TemporalPager(object):
    """A pager that skips by time, rather than number of items.  The advantage
    is that a client can browse back arbitrarily far without the O(n) cost that
    LIMIT clauses impose.  The downside is that it's not feasible to show a
    list of pages any more, so it's difficult to express where the user is
    within the items or even to provide a "back one page" link.

    The API is similar to `DiscretePager` above, but not interchangeable.

    This class uses the 'timeskip' query parameter rather than 'skip', to help
    tell which type of pager is being used.
    """

    pager_type = 'temporal'
    item_count = None

    def __init__(self, query, page_size, column_name, formdata={}):
        """Create a pager.

        `column_name` is the name of the datetime column in the query, to be
        used for adding the offset and figuring out where the next page starts.

        Other arguments are the same as for `DiscretePager`.
        """
        self.formdata = formdata.copy()
        self.formdata.pop('skip', None)  # get rid of cruft, just in case

        # Find the column for the table in question
        table = query.column_descriptions[0]['expr']
        time_column = getattr(table, column_name)

        self.timeskip = _datetime_from_query(
            self.formdata.pop('timeskip', None))
        if self.timeskip:
            query = query.filter(time_column <= self.timeskip)

        # Get one extra, for figuring out where the next page starts, and
        # whether one exists
        self.items = query.limit(page_size + 1).all()
        self.visible_count = len(self.items)
        self.next_item = None
        self.next_item_timeskip = None
        if len(self.items) > page_size:
            self.next_item = self.items.pop()
            self.next_item_timeskip = getattr(self.next_item, column_name)

        self.page_size = page_size

    def __iter__(self):
        return iter(self.items)

    def formdata_for(self, timeskip):
        formdata = self.formdata.copy()
        # timeskip=None doesn't get put in the query
        if timeskip:
            formdata['timeskip'] = _datetime_to_query(timeskip)
        return formdata

    @property
    def is_last_page(self):
        return self.next_item is None
