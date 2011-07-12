<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Site Log</%def>
<%def name="panel_icon()">${lib.icon('book-bookmark')}</%def>

<table class="log">
<thead>
  <tr>
    <th>Level</th>
    <th>Time</th>
    <th>IP Address</th>
    <th>Admin User</th>
    <th>Privileges Used</th>
    <th>Affected User</th>
    <th>Log Message</th>
    <th>Reason</th>
  </tr>
</thead>
<tbody>
<% curr = "even"
off = "odd" %>
% for record in records:
  <% curr, off = off, curr %>
  <tr class="${curr}">
    <td>${lib.levelicon(record.level)} ${lib.levelname(record.level)}</td>
    <td>${lib.time(record.timestamp)}</td>
    % if record.ipaddr:
    <td>${record.ipaddr}</td>
    % else:
    <td>None</td>
    % endif
    % if record.user:
    <td>${record.user.name}</td>
    % else:
    <td>—</td>
    % endif
    <% privs = ', '.join([priv.name for priv in record.privileges]) %>
    <td>${privs}</td>
    % if record.target_user:
    <td>${record.target_user.name}</td>
    % else:
    <td>—</td>
    % endif
    <td>${record.message}</td>
    <td>${record.reason}</td>
  </tr>
% endfor
</tbody>
</table>
