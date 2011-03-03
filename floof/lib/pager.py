"""Classes for dividing a number of items into pages and showing controls for
navigating between such.
"""
from __future__ import division

from calendar import timegm
from collections import namedtuple
from datetime import datetime
import math

import pytz

# XXX need to limit how much skipping we're willing to do here
class Pager(object):
    def __init__(self, query, page_size, skip, formdata={}, radius=3, count_pages=False):
        """Create a pager.

        `query` is assumed to be a SQLAlchemy query object, without any limits
        applied; this class will do that for you.  The rest, hopefully, are
        self-explanatory.
        """
        # Check for some unwanted form data keys that are special to Routes
        if any(key in formdata for key in ('controller', 'action', 'anchor',
            'host', 'protocol', 'qualified', 'sub_domain')):

            raise KeyError("Your formdata contains a special Routes key.  :(")

        self.formdata = formdata.copy()

        # Get one extra, for figuring out where the next page starts, and
        # whether one exists
        self.items = query.limit(page_size + 1).offset(skip).all()
        self.next_item = None
        if len(self.items) > page_size:
            self.next_item = self.items.pop()

        self.skip = skip
        self.page_size = page_size
        self.current_page = skip / page_size
        self.radius = radius

        if count_pages:
            self.item_count = query.count()
            self.last_page = int(math.ceil(
                self.item_count / self.page_size - 1))
        else:
            self.item_count = None
            self.last_page = None

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
        if before_current - delta <= 2:
            # <= 2 is so we don't have "1 ... 3 4 5"
            pages.extend(range(0, before_current + 1))
        else:
            pages.append(0)
            pages.append(None)
            pages.extend(range(
                before_current - delta, before_current + 1))

        # Current
        pages.append(self.current_page)

        # Current through end
        if self.last_page is None:
            # Don't know the last page.  Show one more and ..., if appropriate
            if self.next_item:
                pages.append(after_current)
                pages.append(None)
            return pages

        if after_current + delta >= self.last_page - 2:
            pages.extend(range(
                after_current, self.last_page + 1))
        else:
            pages.extend(range(after_current, after_current + delta + 1))
            pages.append(None)
            pages.append(self.last_page)

        return pages

    @property
    def is_last_page(self):
        return self.next_item is None
