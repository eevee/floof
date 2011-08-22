<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Register</%def>
<%def name="script_dependencies()">
    ${h.javascript_link('/js/detect-timezone.js')}
    ${h.javascript_link('/js/timezone-guesser.js')}
</%def>

<h1>Register with OpenID</h1>

${lib.secure_form(request.route_url('account.register'))}
<dl>
    <dt>Registering from:</dt>
    % if identity_webfinger:
        <dd><tt>${identity_webfinger} (${identity_url})</tt></dd>
    % else:
        <dd><tt>${identity_url}</tt></dd>
    % endif
    ${lib.field(form.username)}
    ${lib.field(form.email)}
    ${lib.field(form.timezone)}

    <dd><button type="submit">OK, register!</button></dd>
</dl>
${h.end_form()}
