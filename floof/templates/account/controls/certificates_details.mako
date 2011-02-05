<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">SSL Certificate Detail</%def>
<%def name="panel_icon()">${lib.icon('key')}</%def>

<h2>Detailed Info for Certificate ID ${c.cert.id}</h2>
<p><a href="${url(controller='controls', action='certificates')}">Go back to concise view</a></p>
<dl>
    <dt>Certificate ID ${c.cert.id}</dt>
    % if c.cert.revoked:
    <dd>Revoked at: ${lib.time(c.cert.revoked_time)}</dd>
    % elif c.cert.expired:
    <dd>Expired at: ${lib.time(c.cert.expiry_time)}</dd>
    % endif
    <dd><pre>${c.cert.details}</pre></dd>
</dl>
<p><a href="${url(controller='controls', action='certificates')}">Go back to concise view</a></p>
