"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
from pylons import url
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
