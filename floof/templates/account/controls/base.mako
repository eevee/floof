<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">${self.panel_title()} - Control panel</%def>

<h1>${self.panel_icon()} Control panel » ${self.panel_title()}</h1>

<ul id="control-panel-navigation">
    % for action, icon, title in [ \
        ('index',           'fruit',        u'Index??'), \
        ('relationships',   'users',        u'Watches'), \
    ]:
    % if action == c.current_action:
    <li class="selected">${lib.icon(icon)} ${title}</li>
    % else:
    <li><a href="${url(controller='controls', action=action)}">${lib.icon(icon)} ${title}</a></li>
    % endif
    % endfor
</ul>

<div id="control-panel-content">
${next.body()}
