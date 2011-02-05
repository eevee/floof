<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">SSL Certificates</%def>
<%def name="panel_icon()">${lib.icon('key')}</%def>

${h.secure_form(url.current())}

<h2>Your Currently Active Certificates</h2>
% if not c.user.valid_certificates:
<p>You have no active certificates.</p>
% else:
<table>
    <tr>
        <th>ID</th>
        <th>Key Bit Length</th>
        <th>Created Time</th>
        <th>Expiry Time</th>
        <th>Time Until Expiry</th>
        <th>Certificate Details</th>
        <th>Download Certificate</th>
        <th>Revoke Certificate</th>
    </tr>
    % for cert in c.user.valid_certificates:
    <tr>
        <td>${cert.id}</td>
        <td>${cert.bits}</td>
        <td>${lib.time(cert.created_time)}</td>
        <td>${lib.time(cert.expiry_time)}</td>
        <td>${lib.longtimedelta(cert.expiry_time)}</td>
        <td><a href="${url(controller='controls', action='certificates_details', id=cert.id)}" title="Full text of the certificate">Details</a></td>
        <td><a href="${url(controller='controls', action='certificates_download_prep', id=cert.id)}" title="Download this certificate (private and public parts) in PKCS12 format">Download...</a></td>
        <td><a href="${url(controller='controls', action='certificates_revoke', id=cert.id)}" title="Download this certificate (private and public parts) in PKCS12 format">Revoke...</a></td>
    </tr>
    % endfor
</table>
% endif

<h2>Generate New Certificate</h2>
<dl>
  ${lib.field(c.form.days)}
</dl>
${c.form.generate()}

<h2>Your Revoked and Expired Certificates</h2>
% if not c.user.invalid_certificates:
<p>You have no revoked or expired certificates.</p>
% else:
<table>
    <tr>
        <th>ID</th>
        <th>Key Bit Length</th>
        <th>Created Time</th>
        <th>Expiry Time</th>
        <th>Revocation Time</th>
        <th>Certificate Details</th>
        <th>Download Certificate</th>
    </tr>
    % for cert in c.user.invalid_certificates:
    <tr>
        <td>${cert.id}</td>
        <td>${cert.bits}</td>
        <td>${lib.time(cert.created_time)}</td>
        <td>${lib.time(cert.expiry_time)}</td>
        % if cert.revoked_time is None:
        <td>Expired (Not Revoked)</td>
        % else:
        <td>${lib.time(cert.revoked_time)}</td>
        % endif
        <td><a href="${url(controller='controls', action='certificates_details', id=cert.id)}" title="Full text of the certificate">Details</a></td>
        <td><a href="${url(controller='controls', action='certificates_download_prep', id=cert.id)}" title="Download this certificate (private and public parts) in PKCS12 format">Download...</td>
    </tr>
    % endfor
</table>
% endif

${h.end_form()}
