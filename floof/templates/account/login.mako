<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<h1>Log in or register with OpenID</h1>

% if c.user:
<p>Already logged in as ${c.user.display_name}.</p>
% else:
${h.secure_form(url(controller='account', action='login_begin'))}
<p>
    ${lib.field(c.form.identifier)}
    <input type="submit" value="Log in">
</p>
${h.end_form()}
% endif
