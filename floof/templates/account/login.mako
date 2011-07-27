<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Login or Register or Re-authenticate</%def>

% if user:
    % if 'openid' in auth.satisfied:
        <h1>Re-authenticate with OpenID</h1>
        <p>Authenticate again to refresh your OpenID token.  Its present
        age is:
        <span class="monospace">${str(auth.openid_age).split('.')[0]}</span>.
        </p>
    % else:
        <h1>Re-Authenticate with OpenID</h1>
        <p>Authenticate with OpenID to increase the security level of your
        current session.  This is necessary to perfom certain sensitive or
        administrative actions.</p>
    % endif
    <p>Logged in as ${user.display_name}.</p>
% elif auth.pending_user:
    <h1>Partially Authenticated: ${auth.pending_user.name}</h1>
    % if 'cert' in auth.satisfied:
        <p>You have successfully authenticated with an SSL client
        certificate, which has identified you as
        ${auth.pending_user.name}.  However, your account authentication
        settings have disabled certificate login, so you'll need to log in
        with your OpenID.</p>
        <p>To stop authenticating via SSL certificate you must instruct
        your web browser to stop sending the certificate.</p>
    % else:
        <p>You have successfully authenticated with OpenID, which has
        identified you as ${auth.pending_user.name}.  However, your
        account authentication settings require SSL client certificate
        authentication to log in.</p>
        ${lib.secure_form(request.route_url('account.logout'))}
            <p>Click the following button to purge all satisfied
            authentication mechanisms.</p>
            <p><input type="submit" value="Purge Authentication"></p>
        ${h.end_form()}
    % endif
% else:
    <h1>Log in or register with OpenID</h1>
% endif
${lib.secure_form(request.route_url('account.login_begin'))}
    <p>
    ${lib.field(form.openid_identifier)}
    ${form.return_key() | n}
    <input type="submit" value="Log in" />
    </p>
${h.end_form()}
