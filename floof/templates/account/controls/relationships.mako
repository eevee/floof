<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Watches</%def>
<%def name="panel_icon()">${lib.icon('users')}</%def>

## Only show art watches for now; the others don't have a remote chance of
## working yet
% for rel_type, rel_label in [ \
    (u'watch.art', u'Watching art') ]:
<h2>${rel_label}</h2>
% if c.relationships[rel_type]:
<table class="user-list">
    % for user in c.relationships[rel_type]:
    <tr>
        <td>${lib.user_link(user)}</td>
    % endfor
</ul>
% else:
<p>Nobody.</p>
% endif
% endfor
