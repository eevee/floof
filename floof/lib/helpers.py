"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
from __future__ import absolute_import
import re
import unicodedata

import lxml.html
import lxml.html.clean
import markdown
from webhelpers.html import escape, HTML, literal, tags, url_escape
# XXX replace the below with tags.?
from webhelpers.html.tags import form, end_form, hidden, submit
from webhelpers.html.tags import javascript_link, stylesheet_link
from webhelpers.util import update_params

from pyramid.security import has_permission


def render_rich_text(raw_text, chrome=False):
    """Takes a unicode string of Markdown source.  Returns literal'd HTML."""

    # First translate the markdown
    md = markdown.Markdown(
        extensions=[],
        output_format='html',
    )

    html = md.convert(raw_text)

    # Then sanitize the HTML -- whitelisting only, thanks!
    # Make this as conservative as possible to start.  Might loosen it up a bit
    # later.
    fragment = lxml.html.fragment_fromstring(html, create_parent='div')

    if chrome:
        # This is part of the site and is free to use whatever nonsense it wants
        allow_tags = None
    else:
        # This is user content; beware!!
        allow_tags = [
            # Structure
            'p', 'div', 'span', 'ul', 'ol', 'li',
            # Tables
            #'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
            # Embedding
            'a',
            # Oldschool styling
            'strong', 'b', 'em', 'i', 's', 'u',
        ]

    cleaner = lxml.html.clean.Cleaner(
        scripts = True,
        javascript = True,
        comments = True,
        style = True,
        links = True,
        meta = True,
        page_structure = True,
        #processing_instuctions = True,
        embedded = True,
        frames = True,
        forms = True,
        annoying_tags = True,
        safe_attrs_only = True,

        remove_unknown_tags = False,
        allow_tags = allow_tags,
    )
    cleaner(fragment)

    # Autolink URLs
    lxml.html.clean.autolink(fragment)

    # And, done.  Flatten the thing and return it
    friendly_html = lxml.html.tostring(fragment)
    # We, uh, need to remove the <div> wrapper that lxml imposes.
    # I am so sorry.
    match = re.match(r'\A<div>(.*)</div>\Z', friendly_html, flags=re.DOTALL)
    if match:
        friendly_html = match.group(1)

    return literal(friendly_html)


def friendly_serial(serial):
    """Returns a more user-friendly rendering of the passed cert serial."""

    result = ''
    length = min(len(serial), 10)
    start = len(serial) - length
    for i, char in enumerate(serial[start:]):
        result += char
        if i % 2 == 1:
            result += ':'

    return result[:-1]


def reduce_display_name(name):
    """Return a reduced version of a display name for comparison with a
    username.
    """
    # Strip out diacritics
    name = ''.join(char for char in unicodedata.normalize('NFD', name)
                   if not unicodedata.combining(char))

    name = re.sub(r'\s+', '_', name)
    name = name.lower()

    return name
