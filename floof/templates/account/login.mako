<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

% if c.user:
<p>Already logged in as ${c.user.display_name}.</p>
% else:
    % if c.auth.pending_user:
        <h1>Partially Authenticated: ${c.auth.pending_user.name}</h1>
        % if 'cert' in c.auth.satisfied:
            <p>You have successfully authenticated with an SSL client
            certificate, which has identified you as
            ${c.auth.pending_user.name}.  However, your account authentication
            settings have disabled certificate login, so you'll need to log in
            with your OpenID.</p>
            <p>To stop authenticating via SSL certificate you must instruct
            your web browser to stop sending the certificate.</p>
        % else:
            <p>You have successfully authenticated with OpenID, which has
            identified you as ${c.auth.pending_user.name}.  However, your
            account authentication settings require SSL client certificate
            authentication to log in.</p>
            ${h.secure_form(url(controller='account', action='logout'))}
            <p>Click the following button to purge all satisfied
            authentication mechanisms.</p>
            <p><input type="submit" value="Purge Authentication"></p>
            ${h.end_form()}
        % endif
    % endif
    % if not 'openid' in c.auth.satisfied:
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
