<%inherit file="base.mako" />

<h1>Log in or register with OpenID</h1>

${h.form(url(controller='account', action='login_begin'))}
<p>
    <input type="text" name="openid_identifier" value="${c.attempted_openid if c.attempted_openid else u''}">
    <input type="submit" value="Log in">
</p>
${h.end_form()}
