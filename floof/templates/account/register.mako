<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<h1>Register with OpenID</h1>

${h.form(url(controller='account', action='register'))}
<dl>
    <dt>Registering from</dt>
    <dd><tt>${c.identity_url}</tt></dd>
    ${lib.field(c.form.username)}

    <dd><button type="submit">OK, register!</button></dd>
</dl>
${h.end_form()}
