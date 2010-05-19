<%inherit file="base.mako" />

<h1>Register with OpenID</h1>

% if c.username_error == 'taken':
<p class="error">Your username is already taken.  Please enter another one below.</p>
% elif c.username_error == 'missing':
<p class="error">Please select a username below.</p>
% elif c.username_error == 'invalid':
<p class="error">Your username must be 1–24 characters and contain only lowercase letters, numbers, and underscores.  Please select another below.</p>
% endif

${h.form(url(controller='account', action='register'))}
<dl>
    <dt>Registering from</dt>
    <dd><code>${c.identity_url}</code></dd>
    <dt>Username</dt>
    <dd><input type="text" name="username" value="${c.username}"></dd>

    <dd><button type="submit">OK, register!</button></dd>
</dl>
${h.end_form()}
