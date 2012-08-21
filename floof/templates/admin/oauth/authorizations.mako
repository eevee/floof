<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">OAuth Authorizations</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>


<table class="oauth striped">
<thead>
    <tr>
        <th>Authorizing User</th>
        <th>Scopes</th>
        <th>Client Name</th>
        <th>Client Owner</th>
        <th>App Type</th>
        <th>Site URI</th>
        <th>Created</th>
        <th>Revoke</th>
    </tr>
</thead>
<tbody>
% for authz in authorizations:
    <% client = authz.client %>
    <tr>
        <td>${lib.user_link(authz.user)}</td>
        <td>${' '.join(authz.scopes)}</td>
        <td><a href="${request.route_url('admin.oauth.clients.edit', client=client)}">${lib.limit_text(client.name, 40)}</a></td>
        <td>${lib.user_link(client.user)}</td>
        <td>${u'Web Server' if client.type == u'web' else u'Native or Mobile'}</td>
        % if client.site_uri:
            <td><a href="${client.site_uri}">${lib.limit_text(client.site_uri, 40)}</a></td>
        % else:
            <td>N/A</td>
        % endif
        <td>${lib.time(client.created)}</td>
        <td><a href="${request.route_url('admin.oauth.authorizations.revoke', authz=authz)}">Revoke...</a></td>
    </tr>
% endfor
</tbody>
</table>

${lib.discrete_pager(authorizations)}
