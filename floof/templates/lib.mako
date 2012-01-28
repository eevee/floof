<%! import hashlib %>
<%! import math %>
<%! import pytz %>
<%! import wtforms.widgets %>
<%! from datetime import datetime %>

<%def name="avatar(request, user, size=120)">\
<%
    GRAVATAR_URL = "https://secure.gravatar.com/avatar/{hash}?r=r&s={size}&d=mm"
    if user.avatar:
        src=request.route_url('filestore', class_=u'avatar', key=user.avatar.hash)
    else:
        email = user.email or ''
        hash = hashlib.md5(email.lower()).hexdigest()
        src = GRAVATAR_URL.format(hash=hash, size=size)
%>\
<img class="avatar" width="${size}" height="${size}" alt="${user_name(user)}" src="${src}" />\
</%def>

<%def name="icon(which, alt='')">\
<img src="${request.static_url("floof:public/icons/{which}.png".format(which=which))}" alt="${alt}">\
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


## User handling
<%def name="date(t)">\
${request.user.localtime(t).strftime('%Y-%m-%d')}\
</%def>

<%def name="time(t)">\
${request.user.localtime(t).strftime('%A, %d %B %Y at %H:%M %Z')}\
</%def>

<%def name="shorttime(t)">\
${request.user.localtime(t).strftime('%Y-%m-%d %H:%M %Z')}\
</%def>

<%def name="timedelta(td)">\
${ "{0:.02f}".format( td.seconds + td.microseconds / 1000000.0 ) }s\
</%def>

<%def name="longtimedelta(t1)">\
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
%>\
${"{0} days, {1} hours, {2} mins".format(td.days, hours, mins)}\
</%def>

<%def name="user_name(user, show_trivial_username=False)">
% if user.display_name is None:
${user.name}\
% elif user.has_trivial_display_name and not show_trivial_username:
${user.display_name}\
% else:
${user.display_name} (${user.name})\
% endif
</%def>

<%def name="user_link(user, show_trivial_username=False)">
<a href="${request.route_url('users.view', user=user)}">\
% if user.display_name is None or (user.has_trivial_display_name and not show_trivial_username):
${user_name(user, show_trivial_username)}</a>\
% else:
${user.display_name}</a> (${user.name})\
% endif
</%def>

<%def name="user_panel(user)">
<a href="${request.route_url('users.view', user=user)}" class="user-panel">
    ${user.display_name}
</a>
</%def>


## Standard form rendering
<%def name="secure_form(*args, **kwargs)">
${h.tags.form(*args, **kwargs)}
${h.tags.hidden('csrf_token', value=request.session.get_csrf_token(), id=None)}
</%def>

<%def name="field(form_field, hint_text=None, **kwargs)">\
% if isinstance(form_field.widget, wtforms.widgets.CheckboxInput):
<dd>
    ${form_field(**kwargs) | n} ${form_field.label() | n}
% else:
<dt>${form_field.label() | n}</dt>
<dd>
    ${form_field(**kwargs) | n}
% endif
    % if hint_text:
    <p class="standard-form-hint">${hint_text}</p>
    % endif
    ${field_errors(form_field)}
</dd>
</%def>

<%def name="field_errors(form_field)">\
% for error in form_field.errors:
<p class="form-error">${error | n}</p>
% endfor
</%def>


## Prints a short summary of a resource; used as the header in commenting
<%def name="resource_summary(resource)">
% if resource.type == u'artwork':
<p><a href="${request.route_url('art.view', artwork=resource.member)}">Return</a></p>
% endif
</%def>

<%def name="cert_serial(cert)">\
<span class="monospace">${h.friendly_serial(cert.serial)}</span>\
</%def>


## Rendering for lib.pager.Pager objects
<%def name="discrete_pager(pager, temporal_column_name=None)">
## When `temporal_column_name` is given, discrete pagers that have reached
## their maximum allowed limit will switch to temporal pagers.  Used for
## GallerySieve
<ol class="pager">
% if pager.current_page > 0:
    <li class="pager-first">
        <a href="${h.update_params(request.path_url, **pager.formdata_for(int(pager.current_page - 1) * pager.page_size))}">
            ←
        </a>
    </li>
    <li class="pager-first">
        <a href="${h.update_params(request.path_url, **pager.formdata_for(0))}">
            ⇤
        </a>
    </li>
% else:
    <li class="pager-first elided">←</li>
    <li class="pager-first elided">⇤</li>
% endif
% for page in pager.pages():
    % if page is None:
    <li class="elided">…</li>
    % elif page == pager.current_page:
    <li class="current">
        ${int(page + 1)}${u'½' if page != int(page) else u''} <br>
      <!--
      % if pager.item_count:
        % if pager.item_count > pager.skip + 1:
        #${pager.skip + 1}–${min(pager.skip + pager.page_size, pager.item_count)}
        % else:
        ${pager.item_count}
        % endif
        of ${pager.item_count}
      % else:
        #${pager.skip + 1}–${pager.skip + pager.visible_count}
      % endif
      -->
    </li>
    % else:
    <li>
        <a href="${h.update_params(request.path_url, \
            **pager.formdata_for(page * pager.page_size))}">
            ${page + 1}
        </a>
    </li>
    % endif
% endfor
% if temporal_column_name and pager.is_last_allowable_page:
<li>
    <a href="${h.update_params(request.path_url, \
        **pager.formdata_for_temporal(temporal_column_name))}">More →</a>
</li>
% endif
% if pager.next_item:
    <li class="pager-last">
        <a href="${h.update_params(request.path_url, **pager.formdata_for(int(pager.current_page + 1) * pager.page_size))}">
            →
        </a>
    </li>
% else:
    <li class="pager-last elided">→</li>
% endif
% if pager.next_item and pager.item_count:
    <li class="pager-last">
        <a href="${h.update_params(request.path_url, **pager.formdata_for(pager.last_page * pager.page_size))}">
            ⇥
        </a>
    </li>
% else:
    <li class="pager-last elided">⇥</li>
% endif
</ol>
</%def>

<%def name="temporal_pager(pager)">
<ol class="pager">
    % if pager.timeskip:
    <li>
        <a href="${h.update_params(request.path_url, \
            **pager.formdata_for(None))}">⇤ Newest</a>
    </li>
    <li class="elided">…</li>
    <li class="current">
        ${time(pager.timeskip)}<br>
        and earlier
    </li>
    % else:
    <li>Newest</li>
    % endif

    % if not pager.is_last_page:
    <li>
        <a href="${h.update_params(request.path_url, \
            **pager.formdata_for(pager.next_item_timeskip))}">More →</a>
    </li>
    % endif
</ol>
</%def>
