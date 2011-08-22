<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Log in or register</%def>

<% auth = object() %>
% if request.user:
<h1>Hey!  You're already logged in</h1>
<p>We already know you as <code>${request.user.name}</code>.</p>
<p>If you'd like to link another OpenID to your account, feel free to enter it below.</p>
<p>Or, log in as yourself again to refresh your token and be more authorized, whatever that means.</p>
% elif 0 and auth.pending_user:
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
