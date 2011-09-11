<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">SSL Certificates</%def>
<%def name="panel_icon()">${lib.icon('key')}</%def>

<h2>About Certificates</h2>
<p>SSL/TLS Client Certificates are small files that allow you to
authenticate to online applications in a manner that is more resistant
to unauthorized use than passwords.  As implemented here, they also
provide some additional protection against session hijacking.</p>

<p>While this page is aimed at <strong>advanced users</strong> who
don't mind potentially having to fiddle around with their browser's
internal settings, feel free to have a play around.  You can't break
anything by fiddling about here.</p>

<p>Once you've got the hang of it and have a certificate successfully
installed, you can change your
<a href="${request.route_url('controls.auth')}">
Authentication Options</a> to require that you present that certificate
to log on at all.</p>

<h2>Generate New Certificate</h2>
<div class="halfsplit">
    ${lib.secure_form(request.path_url)}
    <h3>Generate Certificate in Browser</h3>
    <p>This will cause your browser to generate and install a certificate
    automatically.</p>
    <p>This is the easiest option, but it's not supported by all
    browsers.</p>
    <p>The latest versions of Firefox, Chrome and Opera should handle
    this fine.  Internet Explorer (any version) will not work.  Safari
    has not been tested.</p>
    <p>After generation, you should try to export your certificate from
    your browser or operating system's certificate store.  This is useful
    as a backup and will allow you to import and use the one certificate
    on multiple computers.</p>
    <dl>
        ${lib.field(form.days)}
        ${lib.field(form.pubkey)}
    </dl>
    ${form.generate_browser()}
    ${h.end_form()}
</div>
<div class="halfsplit">
    ${lib.secure_form(request.route_url('controls.certs.generate_server', name=request.user.name))}
    <h3>Generate Certificate on Server</h3>
    <p>This will return a PKCS12 certificate file for download and
    manual installation.</p>
    <p>Is universally browser-compatible, but you'll have to work out
    how to install the certificate yourself.</p>
    <p>The Friendly Name and Passphrase are optional.  Specifing a
    passphrase may fix import errors on certain buggy platforms.</p>
    <p>Be sure to save the file when prompted -- you will not be able to
    download the generated private key again.</p>
    <dl>
        ${lib.field(form.days)}
        ${lib.field(form.name)}
        ${lib.field(form.passphrase)}
    </dl>
    ${form.generate_server()}
    ${h.end_form()}
</div>

<h2 style="clear:both;">Your Currently Active Certificates</h2>
% if not request.user.valid_certificates:
<p>You have no active certificates.</p>
% else:
<table>
    <tr>
        <th>ID</th>
        <th>Key Bits</th>
        <th>Created Time</th>
        <th>Expiry Time</th>
        <th>Time Until Expiry</th>
        <th>Details</th>
        <th>Download</th>
        <th>Revoke</th>
    </tr>
    % for cert in request.user.valid_certificates:
    <tr>
        <td>${lib.cert_serial(cert.serial)}</td>
        <td>${cert.bits}</td>
        <td>${lib.time(cert.created_time)}</td>
        <td>${lib.time(cert.expiry_time)}</td>
        <td>${lib.longtimedelta(cert.expiry_time)}</td>
        <td><a href="${request.route_url('controls.certs.details', id=cert.id)}" title="Full text of the certificate">Details</a></td>
        <td><a href="${request.route_url('controls.certs.download', id=cert.id, name=request.user.name)}" title="Download this certificate (public component only) in PEM-encoded X.509 format">Download</a></td>
        <td><a href="${request.route_url('controls.certs.revoke', id=cert.id)}" title="Revoke this certificate">Revoke...</a></td>
    </tr>
    % endfor
</table>
% endif

<h2>Your Revoked and Expired Certificates</h2>
% if not request.user.invalid_certificates:
<p>You have no revoked or expired certificates.</p>
% else:
<table>
    <tr>
        <th>ID</th>
        <th>Key Bits</th>
        <th>Created Time</th>
        <th>Expiry Time</th>
        <th>Revocation Time</th>
        <th>Details</th>
        <th>Download</th>
    </tr>
    % for cert in request.user.invalid_certificates:
    <tr>
        <td>${lib.cert_serial(cert.serial)}</td>
        <td>${cert.bits}</td>
        <td>${lib.time(cert.created_time)}</td>
        <td>${lib.time(cert.expiry_time)}</td>
        % if cert.revoked_time is None:
        <td>Expired (Not Revoked)</td>
        % else:
        <td>${lib.time(cert.revoked_time)}</td>
        % endif
        <td><a href="${request.route_url('controls.certs.details', id=cert.id)}" title="Full text of the certificate">Details</a></td>
        <td><a href="${request.route_url('controls.certs.download', id=cert.id, name=request.user.name)}" title="Download this certificate (public component only) in PEM-encoded X.509 format">Download</td>
    </tr>
    % endfor
</table>
% endif
