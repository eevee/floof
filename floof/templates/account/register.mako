<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Register</%def>
<%def name="script_dependencies()">
    ${h.javascript_link('/js/detect-timezone.js')}
    ${h.javascript_link('/js/timezone-guesser.js')}
</%def>

% if request.user:
<section>
    <h1>Add a new login to your account</h1>

    <p>You're already logged in as ${lib.user_link(request.user)}, and you're trying to identify as <code>${identity_webfinger or identity_url}</code>.</p>
    <p>You can link this to your account as a secondary identity.  That way, if you lose access to your main identity, you can still log in.</p>

    ${lib.secure_form(request.route_url('account.add_identity'))}
    <p><button>Sounds good!  Link me up</button></p>
    ${h.end_form()}

    <p>Or did you want to create an entirely new account?</p>
</section>
% endif


<section>
<h1>Register a new account</h1>

<aside class="sidebar">
    <h1>Names</h1>
    <p>Your <dfn>username</dfn> appears in your userpage URL.  It has to be unique, you can't change it, and it can only use letters, numbers, and underscores.</p>
    <p>You can also pick a <dfn>display name</dfn> which shows next to your art and comments.  It can be anything you want and can be changed at any time.</p>
    <p>If your display name doesn't look anything like your username, we'll show them both, like this: <code><strong>Awesome Guy</strong> (sephirothluvr2016)</code></p>
    <p>But if your display name is just your username with some capitals and spaces, that's all we'll show: <code><strong>SephirothLuvr2016</strong></code></p>
    <p>Confused?  Just leave "display name" blank, and you can worry about it later.</p>
</aside>

${lib.secure_form(request.route_url('account.register'), style="overflow: hidden;")}
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
    ${lib.field(form.username, hint_text=u"up to 24 characters.  lowercase letters, numbers, underscores.  can't be changed!")}
    ${lib.field(form.display_name, hint_text=u"optional.  up to 24 characters.  whatever you want.  can change at any time.")}
    ${lib.field(form.email, hint_text=u"we don't check this yet")}
    ${lib.field(form.timezone, hint_text=u"our best guess")}

    <dd><button type="submit">OK, register!</button></dd>
</dl>
${h.end_form()}
</section>
