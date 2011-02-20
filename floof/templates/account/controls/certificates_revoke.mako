<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Revoke SSL Certificate ID ${c.cert.id}</%def>
<%def name="panel_icon()">${lib.icon('key--minus')}</%def>

${h.secure_form(url.current())}
<h2>Permanently Revoke Certificate ID ${c.cert.id}</h2>
<p>Are you absolutely sure that you wish to <strong>permanently revoke</strong>
the certificate below?  You will no longer be able to log in with this
certificate.<p>
% if c.cert.serial == c.auth.cert_serial and 'cert' in c.auth.satisfied_mechanisms:
<p>You are currently using this certificate.  Revoking it will
automatically log you out.  If you still wish to continue, please
ensure that you have an alternate way of logging in.</p>
    % if c.will_override_auth == 1:
    <p>This is your last valid certificate.  If you revoke it, then your
    choice of authentication mechanism will be overwritten to
    &quot;Certificate OR OpenID&quot; at next login.</p>
    % endif
% endif
<p>This action cannot be undone.</p>

${c.form.ok()}
${c.form.cancel()}

<h2>Certificate Details</h2>
<dl>
    <dt>ID</dt>
    <dd>${lib.cert_serial(c.cert.serial)}</dd>
    <dt>Full Certificate Serial</dt>
    <dd>${c.cert.serial}</dd>
    <dt>Key Bit Length</dt>
    <dd>${c.cert.bits}</dd>
    <dt>Creation Date</dt>
    <dd>${lib.time(c.cert.created_time)}</dd>
    <dt>Expiry Date</dt>
    <dd>${lib.time(c.cert.expiry_time)}</dd>
    <dt>Time Until Exipry</dt>
    <dd>${lib.longtimedelta(c.cert.expiry_time)}</dd>
</dl>

<h2>Certificate Data</h2>
<pre>${c.cert.details}</pre>

${h.end_form()}
