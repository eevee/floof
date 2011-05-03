<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Register</%def>

<h1>Register with OpenID</h1>

${h.secure_form(url(controller='account', action='register'))}
<dl>
    <dt>Registering from:</dt>
    % if c.identity_webfinger:
        <dd><tt>${c.identity_webfinger} (${c.identity_url})</tt></dd>
    % else:
        <dd><tt>${c.identity_url}</tt></dd>
    % endif
    ${lib.field(c.form.username)}
    ${lib.field(c.form.email)}

    <dd><button type="submit">OK, register!</button></dd>
</dl>
${h.end_form()}
