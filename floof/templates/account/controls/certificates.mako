<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">SSL Certificates</%def>
<%def name="panel_icon()">${lib.icon('certificate')}</%def>

<p><a href="${request.route_url('controls.certs.add')}">
${lib.icon('plus', '+')} Generate New Certificate</a></p>

% if not request.user.certificates:
<p>You have no certificates.</p>
% else:
<table class="certificate">
    <tr>
        <th>ID</th>
        <th>Status</th>
        <th>Key Bits</th>
        <th>Created Date</th>
        <th>Expiry Date</th>
        <th>Time Until Expiry</th>
        <th>Details</th>
        <th>Download</th>
        <th>Revoke...</th>
    </tr>
    <% sort_key = lambda c: (c.valid, c.created_time) %>
    % for cert in sorted(request.user.certificates, key=sort_key, reverse=True):
        <% status = 'Valid' if cert.valid else None %>
        <% status = 'Expired' if cert.expired else status %>
        <% status = 'Revoked' if cert.revoked else status %>
        % if cert.valid:
        <tr class="valid">
        % else:
        <tr class="invalid">
        % endif
            <td>${lib.cert_serial(cert)}</td>
            <td>${status}</td>
            <td>${cert.bits}</td>
            <td>${lib.date(cert.created_time)}</td>
            <td>${lib.date(cert.expiry_time)}</td>
            % if cert.valid:
                <td>${lib.longtimedelta(cert.expiry_time)}</td>
            % else:
                <td>N/A</td>
            % endif
            <td><a href="${request.route_url('controls.certs.details', serial=cert.serial)}" title="Full text of the certificate">Details</a></td>
            <td><a href="${request.route_url('controls.certs.download', serial=cert.serial, name=request.user.name)}" title="Download this certificate (public component only) in PEM-encoded X.509 format">Download</a></td>
            % if cert.valid:
                <td><a href="${request.route_url('controls.certs.revoke', serial=cert.serial)}" title="Revoke this certificate">Revoke...</a></td>
            % else:
                <td>N/A</td>
            % endif
        </tr>
    % endfor
</table>
% endif


<h1>About Certificates</h1>
<p>SSL/TLS Client Certificates are small files that allow you to
authenticate to online applications in a manner that is more resistant
to unauthorized use than passwords.  As implemented here, they also
provide some additional protection against session hijacking.</p>

<p>This feature is aimed at <strong>advanced users</strong> who
don't mind potentially having to fiddle around with their browser's
internal settings.  Howwever, feel free to have a play around on this
page.  You can't break anything by just fiddling about here.</p>

<p>Once you've got the hang of it and have a certificate successfully
installed, you can change your
<a href="${request.route_url('controls.auth')}">
Authentication Options</a> to require that you present that certificate
to log on at all.</p>
