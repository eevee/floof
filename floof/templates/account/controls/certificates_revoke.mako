<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Revoke SSL Certificate
${h.friendly_serial(cert.serial)}</%def>
<%def name="panel_icon()">${lib.icon('key--minus')}</%def>

${lib.secure_form(request.path_url)}
<p>Are you absolutely sure that you wish to <strong>permanently revoke</strong>
the certificate below?  You will no longer be able to log in with this
certificate.<p>

% if cert.serial == request.auth.certificate_serial:
<p>You are currently using this certificate.  Revoking it may
automatically log you out.  If you still wish to continue, please
ensure that you have an alternate way of logging in.</p>
    % if will_override_auth:
    <p>This is your last valid certificate.  If you revoke it, then your
    client certificate authentication method will be overwritten from
    ${request.user.cert_auth} to &quot;Allowed for login&quot; at next
    login.</p>
    % endif
% endif

<p>This action cannot be undone.</p>

${form.ok()}
${form.cancel()}

<h1>Certificate Details</h1>
<dl class="standard-form certificate">
    <dt>ID</dt>
    <dd>${lib.cert_serial(cert)}</dd>
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
    <dt>Certificate Data</dt>
    <dd><pre>${cert.details}</pre></dd>
</dl>

${h.end_form()}
