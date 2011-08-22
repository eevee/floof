<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">${self.panel_title()} - Admin panel</%def>

<h1>${self.panel_icon()} Admin panel » ${self.panel_title()}</h1>

<ul id="control-panel-navigation">
    % for action, icon, title in [ \
        ('dashboard',    'question',         u'Dashboard'), \
        ('log',          'book-bookmark',    u'Log'), \
    ]:
    % if action == current_action:
    <li class="selected">${lib.icon(icon)} ${title}</li>
    % else:
    <li><a href="${request.route_url('admin.' + action)}">${lib.icon(icon)} ${title}</a></li>
    % endif
    % endfor
</ul>

<div id="control-panel-content">
${next.body()}
</div>
