<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

% if c.user:
<p>Already logged in as ${c.user.display_name}.</p>
% else:
    % if c.auth.pending_user:
    <h1>Partially Authenticated: ${c.auth.pending_user.name}</h1>
    <p>You have successfully authenticated with at least one authentication
    mechanism, which has identified you as ${c.auth.pending_user.name}.
    However, your account authentication settings require the satisfaction
    of further or different authentication mechanisms, as shown below.</p>
    <table>
        <tr>
            <th>Authentication Mechanism</th>
            <th>Requirement Level</th>
            <th>Already Satisfied</th>
        </tr>
        % for mech in c.auth.required_mechanisms:
        <tr>
            <td>${mech[0]}</td>
            <td>${mech[1]}</td>
            <% alt = 'Satisfied' if mech[2] else 'Unsatisfied' %>
            <% icon = 'tick' if mech[2] else 'cross' %>
            <td>${lib.icon(icon, alt)}</td>
        </tr>
        % endfor
    </table>
        % if c.auth.can_purge:
        ${h.secure_form(url(controller='account', action='purge_auth'))}
        <p>Click the following button to purge all satisfied
        authentication mechanisms.</p>
        <p>Note: It is not possible to purge certificate authentication
        -- to stop authenticating via SSL certificate you must instruct
        your web browser to stop sending the certificate.</p>
        <p><input type="submit" value="Purge Authentication"></p>
        ${h.end_form()}
        % endif
    % endif
    % if not 'openid' in c.auth.satisfied_mechanisms:
        % if c.auth.pending_user:
        <h1>Authenticate with OpenID</h1>
        % else:
        <h1>Log in or register with OpenID</h1>
        % endif
    ${h.secure_form(url(controller='account', action='login_begin'))}
    <p>
        ${lib.field(c.form.openid_identifier)}
        <input type="submit" value="Log in">
    </p>
    ${h.end_form()}
    % endif
% endif
