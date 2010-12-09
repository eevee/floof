"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
from pylons import url
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
from webhelpers.pylonslib import Flash

import re


_flash = Flash()
def flash(message, icon=None, level='info', **extras):
    """Custom add-to-flash function.  Arbitrary metadata may be saved with a
    message, but the main options are a Fugue icon and the message level:
    success, info, warning, or error.
    """
    # Messages are stored as (message, dict_of_extra_stuff)
    if icon:
        extras['icon'] = icon
    else:
        # XXX base on level
        extras['icon'] = 'finger'

    extras['level'] = level

    _flash((message, extras))


### Helpers for complicated URLs
def _make_url_friendly(title):
    """Given a title that will be used as flavor text in a URL, returns a
    string that will look less like garbage in an address bar.
    """
    return re.sub('[^-_.~a-zA-Z0-9]', '-', title)

def art_url(artwork):
    """Returns the URL for the given piece of artwork."""
    # Only fill in the title if the piece actually has one
    title = dict()
    if artwork.title:
        # RFC 3986 section 2.3 says: letters, numbers, and -_.~ are unreserved
        title['title'] = _make_url_friendly(artwork.title)

    return url(controller='art', action='view', id=artwork.id, **title)

def comment_url(resource, action, comment_id=None, **kwargs):
    """Returns a URL for the named action in the 'comments' controller.

    `resource` is a Resource row.
    """
    urldict = dict(controller='comments', action=action)
    if comment_id:
        urldict['comment_id'] = comment_id

    # Oh no, type-checking, kinda!!
    if resource.type == u'artwork':
        urldict['subcontroller'] = 'art'
        urldict['id'] = resource.member.id
        if resource.member.title:
            urldict['title'] = _make_url_friendly(resource.member.title)

    elif resource.type == u'users':
        # TODO
        raise NotImplementedError

    else:
        raise TypeError("Unknown resource type {0}".format(resource.type))

    urldict.update(kwargs)
    return url(**urldict)
