<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">OAuth Clients</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>


<p><a href="${request.route_url('admin.oauth.clients.add')}">
${lib.icon('plus', '+')} Add OAuth Client</a></p>

<table class="oauth striped">
<thead>
    <tr>
        <th>Name</th>
        <th>Owner</th>
        <th>App Type</th>
        <th>Client Identifier</th>
        <th>Site URI</th>
        <th>Persistent Auths</th>
    </tr>
</thead>
<tbody>
% for client in clients:
    <tr>
        <td><a href="${request.route_url('admin.oauth.clients.edit', client=client)}">${lib.limit_text(client.name, 40)}</a></td>
        <td>${lib.user_link(client.user)}</td>
        <td>${u'Web Server' if client.type == u'web' else u'Native or Mobile'}</td>
        <td class="identifier">${client.identifier}</td>
        % if client.site_uri:
            <td><a href="${client.site_uri}">${lib.limit_text(client.site_uri, 40)}</a></td>
        % else:
            <td>N/A</td>
        % endif
        <td>${len(client.refresh_tokens)}</td>
    </tr>
% endfor
</tbody>
</table>

${lib.discrete_pager(clients)}
