<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Register</%def>
<%def name="script_dependencies()">
    ${h.javascript_link('/js/detect-timezone.js')}
    ${h.javascript_link('/js/timezone-guesser.js')}
</%def>

<section>
<h1>Register a new account</h1>

${lib.secure_form(request.route_url('account.register'))}
<dl class="standard-form">
    <dt>Registering from</dt>
    <dd>
        % if identity_webfinger:
            <code>${identity_webfinger}</code> <br>
            as <code>${identity_url}</code>
        % else:
            <code>${identity_url}</code>
        % endif
    </dd>
    ${lib.field(form.username, hint_text=u"up to 24 characters.  lowercase letters, numbers, underscores")}
    ${lib.field(form.email, hint_text=u"we don't validate this")}
    ${lib.field(form.timezone, hint_text=u"our best guess")}

    <dd><button type="submit">OK, register!</button></dd>
</dl>
${h.end_form()}
</section>
