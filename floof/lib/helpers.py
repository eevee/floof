"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
from pylons import url
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
from webhelpers.pylonslib import Flash


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
