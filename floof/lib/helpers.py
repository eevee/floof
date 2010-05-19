"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
from pylons import url
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
from webhelpers.pylonslib import Flash


_flash = Flash()
def flash(message, icon=None):
    """Custom add-to-flash function that supports remembering an optional icon
    per message.
    """
    # Messages are stored as (message, dict_of_extra_stuff)
    extras = dict()
    if icon:
        extras['icon'] = icon

    _flash((message, extras))
