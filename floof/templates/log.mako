<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%def name="title()">Public Admin Log</%def>

<h1>Public Admin Log</h1>

<p>This is a log of all administrative actions, for purposes of
transparency.</p>

<table class="log">
<thead>
  <tr>
    <th>Time</th>
    <th>Admin User</th>
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
    <td>${lib.time(record.timestamp)}</td>
    % if record.user:
    <td>${record.user.name}</td>
    % else:
    <td>—</td>
    % endif
    % if record.target_user:
    <td>${record.target_user.name}</td>
    % else:
    <td>N/A</td>
    % endif
    <td>${record.message}</td>
    <td>${record.reason}</td>
  </tr>
% endfor
</tbody>
</table>
