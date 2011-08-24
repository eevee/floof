"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
from webhelpers.html import escape, HTML, literal, tags, url_escape
#from webhelpers.html.tags import *
# XXX replace the below with tags.?
from webhelpers.html.tags import form, end_form, hidden, submit, javascript_link
from webhelpers.util import update_params
