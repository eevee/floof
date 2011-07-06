<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Revoke SSL Certificate ID ${cert.id}</%def>
<%def name="panel_icon()">${lib.icon('key--minus')}</%def>

${h.secure_form(request.path_url)}
<h2>Permanently Revoke Certificate ID ${cert.id}</h2>
<p>Are you absolutely sure that you wish to <strong>permanently revoke</strong>
the certificate below?  You will no longer be able to log in with this
certificate.<p>
% if cert.serial == request.auth.certificate_serial and 'cert' in request.auth.satisfied:
<p>You are currently using this certificate.  Revoking it may
automatically log you out.  If you still wish to continue, please
ensure that you have an alternate way of logging in.</p>
    % if will_override_auth:
    <p>This is your last valid certificate.  If you revoke it, then your
    client certificate authentication method will be overwritten from
    ${request.user.cert_auth} to &quot;Allowed&quot; at next login.</p>
    % endif
% endif
<p>This action cannot be undone.</p>

${form.ok()}
${form.cancel()}

<h2>Certificate Details</h2>
<dl>
    <dt>ID</dt>
    <dd>${lib.cert_serial(cert.serial)}</dd>
    <dt>Full Certificate Serial</dt>
    <dd>${cert.serial}</dd>
    <dt>Key Bit Length</dt>
    <dd>${cert.bits}</dd>
    <dt>Creation Date</dt>
    <dd>${lib.time(cert.created_time)}</dd>
    <dt>Expiry Date</dt>
    <dd>${lib.time(cert.expiry_time)}</dd>
    <dt>Time Until Exipry</dt>
    <dd>${lib.longtimedelta(cert.expiry_time)}</dd>
</dl>

<h2>Certificate Data</h2>
<pre>${cert.details}</pre>

${h.end_form()}
