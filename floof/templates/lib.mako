<%! import math %>
<%! import pytz %>
<%! import wtforms.widgets %>
<%! from datetime import datetime %>

<%def name="icon(which, alt='')">\
<img src="${url('icon', which=which)}" alt="${alt}">\
</%def>

<%!
    standard_icons = {
        'uploader': 'arrow-transition-090',
        'by': 'palette-paint-brush',
        'for': 'present-label',
        'of': 'camera-black',
    }
%>
<%def name="stdicon(which)">${icon(standard_icons[which])}</%def>

<%!
    level_icons = {
        10: ('debug', 'document-list'),
        20: ('info', 'information-frame'),
        25: ('admin-public', 'hand-point'),
        26: ('admin-private', 'hand-point'),
        30: ('warning', 'exclamation-diamond-frame'),
        40: ('error', 'cross-circle-frame'),
        50: ('critical', 'exclamation-red-frame'),
    }
%>
<%def name="levelname(level)">${level_icons[level][0]}</%def>
<%def name="levelicon(level)">${icon(level_icons[level][1], level_icons[level][0])}</%def>

<%def name="time(t)">
${c.user.localtime(t).strftime('%A, %d %B %Y at %H:%M %Z')}
</%def>

<%def name="timedelta(td)">\
${ "{0:.02f}".format( td.seconds + td.microseconds / 1000000.0 ) }s\
</%def>

<%def name="longtimedelta(t1)">
<%
if type(t1).__name__ == 'timedelta':
  td = t1
else:
  td = t1 - datetime.now(pytz.utc)
secs = td.seconds
hours = int(math.floor(secs / 60**2))
secs -= hours * 60**2
mins = int(math.floor(secs / 60))
secs -= mins * 60
%>
${"{0} days, {1} hours, {2} mins".format(td.days, hours, mins)}
</%def>

<%def name="user_link(user)">
<a href="${url('user', user=user)}">${user.display_name}</a>
</%def>

<%def name="user_panel(user)">
<a href="${url('user', user=user)}" class="user-panel">
    ${user.display_name}
</a>
</%def>

<%def name="field(form_field, **kwargs)">
% if isinstance(form_field.widget, wtforms.widgets.CheckboxInput):
<dd>
    ${form_field(**kwargs) | n} ${form_field.label() | n}
    ${field_errors(form_field)}
</dd>
% else:
<dt>${form_field.label() | n}</dt>
<dd>
    ${form_field(**kwargs) | n}
    ${field_errors(form_field)}
</dd>
% endif
</%def>

<%def name="field_errors(form_field)">
% for error in form_field.errors:
<p class="form-error">${error | n}</p>
% endfor
</%def>


## Prints a short summary of a resource; used as the header in commenting
<%def name="resource_summary(resource)">
% if resource.type == u'artwork':
<p><a href="${h.art_url(c.discussion.resource.member)}">Return</a></p>
% endif
</%def>
