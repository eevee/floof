"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
from pylons import url
from pylons.controllers.util import redirect as orig_redirect
from webhelpers.html import escape, HTML, literal, tags, url_escape
#from webhelpers.html.tags import *
# XXX replace the below with tags.?
from webhelpers.html.tags import form, end_form, hidden, submit, javascript_link
from webhelpers.pylonslib import Flash
from webhelpers.util import update_params

_flash = Flash()
_default_flash_icons = dict(
    error='exclamation-red-frame',
    warning='exclamation-diamond-frame',
    notice='hand-point-090',
    success='tick-circle',
)
def flash(message, icon=None, level='notice', **extras):
    """Custom add-to-flash function.  Arbitrary metadata may be saved with a
    message, but the main options are a Fugue icon and the message level:
    success, info, warning, or error.
    """
    # Messages are stored as (message, dict_of_extra_stuff)
    if icon:
        extras['icon'] = icon
    else:
        extras['icon'] = _default_flash_icons.get(level, 'finger')

    extras['level'] = level

    _flash((message, extras))
