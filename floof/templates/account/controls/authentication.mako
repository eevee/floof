<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Authentication Options</%def>
<%def name="panel_icon()">${lib.icon('key')}</%def>

${h.secure_form(request.path_url)}
<h2>Authentication Options</h2>
<dl>
    ${lib.field(form.cert_auth)}
</dl>
<p>This is intended for use by <strong>advanced users</strong> only.
There are important things to be aware of when choosing any non-default
option.  Some of them are listed below.</p>
<ol>
    <li>If you choose one of these Authentication Options and log in with
    just a certificate, it will not be possible to log out using the site's
    web interface.  You will have to know how to get your web browser to
    stop authenticating with the certificate.</li>
    <li>If you choose to require certificates for log in or for sensitive
    operations and subsequently all certificates registered against your
    account expire or are revoked, you will automatically be able to log
    in and perform sensitive operations with just your OpenID.  That is,
    your Certificate Authentication Option will be automatically changed to
    &quot;Allow using client certificates for login&quot;.</li>
</ol>
<input type="submit" name="update" value="Update" />
${h.end_form()}
