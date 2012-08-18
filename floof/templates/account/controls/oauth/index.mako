<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">OAuth</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>

<h1>Your Developer Clients</h1>

<p><a href="${request.route_url('controls.oauth.clients.add')}">
${lib.icon('plus', '+')} Add OAuth Client</a></p>

<% clients = request.user.oauth2_clients %>

% if clients:
  <table class="oauth striped">
  <thead>
    <tr>
      <th>Name</th>
      <th>App Type</th>
      <th>Client Identifier</th>
      <th>Default Redirection URI</th>
      <th>Persistent Auths</th>
    </tr>
  </thead>
  <tbody>
  % for client in clients:
    <tr>
      <td><a href="${request.route_url('controls.oauth.clients.edit', client=client)}">${client.name}</a></td>
      <td>${u'Web Server' if client.type == u'web' else u'Native or Mobile'}</td>
      <td class="identifier">${client.identifier}</td>
      <td>${client.redirect_uris[0]}</td>
      <td>${len(client.refresh_tokens)}</td>
    </tr>
  % endfor
  </tbody>
  </table>
% else:
  <p>You have no OAuth clients.  These are only needed if you plan on
  developing an OAuth-enabled API application.</p>
% endif

<h1>Your Persistent Authorizations</h1>

<% authorizations = request.user.oauth2_refresh_tokens %>

% if authorizations:
  <table class="oauth striped">
  <thead>
    <tr>
      <th>Name</th>
      <th>Operator</th>
      <th>Scopes</th>
      <th>Authorized at</th>
      <th>Revoke</th>
    </tr>
  </thead>
  <tbody>
  % for authz in authorizations:
    <tr>
      % if client.site_uri:
        <td><a href="${authz.client.site_uri}">${authz.client.name}</a></td>
      % else:
        <td>${authz.client.name}</td>
      % endif
      <td>${lib.user_link(authz.client.user, show_trivial_username=True)}</td>
      <td>
      % if authz.scopes:
          ${' '.join(authz.scopes)}
      % else:
          &lt;None&gt;
      % endif
      </td>
      <td>${lib.time(authz.created)}</td>
      <td><a href="${request.route_url('controls.oauth.authorizations.revoke', authz=authz)}">Revoke...</a></td>
    </tr>
  % endfor
  </tbody>
  </table>
% else:
  <p>You have no persistent authorizations yet.</p>
  <p>These are created automatically when you authorize a third-party
  application to access some or all of your account.  You will then be able to
  review and revoke that access from this page.</p>
% endif
