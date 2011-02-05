<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Authentication Options</%def>
<%def name="panel_icon()">${lib.icon('key')}</%def>

${h.secure_form(url.current())}
% if c.need_confirmation:
<h2>Confirm Authentication Change</h2>
<p>Changing the the authentication method "${c.form.auth_method.data}"
will cause your current session to immediately log out and you will
require the new authentication credentials to log back in.</p>
<p>Please confirm this action.</p>
<input type="hidden" name="auth_method" value="${c.form.auth_method.data}" />
${c.confirm_form.confirm()}
${c.confirm_form.cancel()}
% else:
<h2>Authentication Options</h2>
<dl>
    ${lib.field(c.form.auth_method)}
</dl>
<p>This is intended for use by advanced users only.  There are important
things to be aware of when choosing any non-default option.  Some of them
are listed below.</p>
<ol>
    <li>If you choose one of these Authentication Options and log in with
    just a certificate, it will not be possible to log out using the site's
    web interface.  You will have to know how to get your web browser to
    stop authenticating with the certificate.</li>
    <li>If you choose one of these options and subsequently all certificates
    registered against your account expire or are revoked, you will
    automatically be able to log in with just your OpenID.  That is, your
    Authentication Option will be automatically changed to
    &quot;Certificate or OpenID&quot;.</li>
</ol>
<input type="submit" name="update" value="Update" />
% endif
${h.end_form()}
