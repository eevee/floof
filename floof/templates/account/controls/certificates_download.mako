<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Download SSL Certificate ID ${c.cert.id}</%def>
<%def name="panel_icon()">${lib.icon('key--arrow')}</%def>

${h.secure_form(url(controller='controls', action='certificates_download', id=c.cert.id, user=c.user.name))}
<h2>Download Certificate ID ${c.cert.id}</h2>
<p><a href="${url(controller='controls', action='certificates')}">Back to certificates listing</a></p>
<p>Here you may specify an optional passphrase against which to encrypt the
certificate before downloading.  Encrypting the certificate file can fix
import failures for some applications (noteably Firefox).</p>

<dl>
    ${lib.field(c.form.passphrase)}
</dl>
${c.form.download()}

${h.end_form()}
