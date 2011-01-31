<%inherit file="/base.mako" />
<%def name="title()">Public Admin Log</%def>

<h1>Pubic Admin Log</h1>

<p>This is a log of all administrative actions, for purposes of
transparency.</p>

<p>Not sure if we want this, but it's here as an example. --epii</p>

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
% for record in c.records:
  <% curr, off = off, curr %>
  <tr class="${curr}">
    <td>${record.timestamp}</td>
    % if record.user:
    <td>${record.user.name}</td>
    % else:
    <td>Anonymous</td>
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