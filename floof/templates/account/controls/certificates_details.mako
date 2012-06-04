<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">SSL Certificate Detail</%def>
<%def name="panel_icon()">${lib.icon('certificate')}</%def>

<section>
    <h1>Detailed Info for Certificate ${lib.cert_serial(cert)}</h1>
    <p><a href="${request.route_url('controls.certs')}">Go back to Certificates List</a></p>
    % if cert.valid:
    <dl class="standard-form certificate valid">
    % else:
    <dl class="standard-form certificate invalid">
    % endif
        <dt>ID</dt>
        <dd>${lib.cert_serial(cert)}</dd>
        <dt>Status</dt>
        % if cert.valid:
            <dd>Valid</dd>
        % elif cert.revoked:
            <dd>Revoked on ${lib.time(cert.revoked_time)}</dd>
        % elif cert.expired:
            <dd>Expired on ${lib.time(cert.expiry_time)}</dd>
        % endif
        <dt>Full Certificate Serial</dt>
        <dd>${cert.serial}</dd>
        <dt>Key Bit Length</dt>
        <dd>${cert.bits}</dd>
        <dt>Creation Date</dt>
        <dd>${lib.time(cert.created_time)}</dd>
        <dt>Expiry Date</dt>
        <dd>${lib.time(cert.expiry_time)}</dd>
        <dt>Time Until Exipry</dt>
        % if cert.expired:
            <dd>Expired</dd>
        % else:
            <dd>${lib.longtimedelta(cert.expiry_time)}</dd>
        % endif
        <dt>Certificate Data</dt>
        <dd><pre>${cert.details}</pre></dd>
    </dl>
    <p><a href="${request.route_url('controls.certs')}">Go back to Certificates List</a></p>
</section>
