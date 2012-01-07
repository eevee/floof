<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">New SSL Certificate</%def>
<%def name="panel_icon()">${lib.icon('plus')}</%def>

<div class="halfsplit">
    ${lib.secure_form(request.path_url)}
    <h1 class="top-heading">Generate Certificate in Browser</h1>
    <dl class="standard-form">
        ${lib.field(browser_form.days)}
        ${lib.field(browser_form.pubkey)}
        <dd class="standard-form-footer">
            <button>Generate in Browser</button>
        </dd>
    </dl>
    ${h.end_form()}
</div>
<div class="halfsplit">
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
</div>

<p style="clear:both;"><a href="${request.route_url('controls.certs')}">Go back to Certificates List</a></p>

<div class="halfsplit">
    <h1>Generate Certificate on Server</h1>
    ${lib.secure_form(request.route_url('controls.certs.generate_server', name=request.user.name))}
    <dl class="standard-form">
        ${lib.field(server_form.days)}
        ${lib.field(server_form.name)}
        ${lib.field(server_form.passphrase)}
        <dd class="standard-form-footer">
            <button>Generate on Server</button>
        </dd>
    </dl>
    ${h.end_form()}
</div>
<div class="halfsplit">
    <p>This will return a PKCS12 certificate file for download and
    manual installation.</p>
    <p>Is universally browser-compatible, but you'll have to work out
    how to install the certificate yourself.</p>
    <p>The Friendly Name and Passphrase are optional.  Specifing a
    passphrase may fix import errors on certain buggy platforms.</p>
    <p>Be sure to save the file when prompted -- you will not be able to
    download the generated private key again.</p>
</div>

<p style="clear:both;"><a href="${request.route_url('controls.certs')}">Go back to Certificates List</a></p>
