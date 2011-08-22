<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">SSL Certificate Detail</%def>
<%def name="panel_icon()">${lib.icon('key')}</%def>

<h2>Detailed Info for Certificate ID ${cert.id}</h2>
<p><a href="${request.route_url('controls.certs')}">Go back to concise view</a></p>
<dl>
    <dt>Certificate ID ${cert.id}</dt>
    % if cert.revoked:
    <dd>Revoked at: ${lib.time(cert.revoked_time)}</dd>
    % elif cert.expired:
    <dd>Expired at: ${lib.time(cert.expiry_time)}</dd>
    % endif
    <dd><pre>${cert.details}</pre></dd>
</dl>
<p><a href="${request.route_url('controls.certs')}">Go back to concise view</a></p>
