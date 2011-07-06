<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Watches</%def>
<%def name="panel_icon()">${lib.icon('users')}</%def>

## Only show art watches for now; the others don't have a remote chance of
## working yet
<h2>Watches</h2>
% if watches:
<table class="user-list">
    % for watch in watches:
    <tr>
        <td>${lib.user_link(watch.other_user)}</td>
    </tr>
    % endfor
</table>
% else:
<p>Nobody.</p>
% endif
