<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">New SSL Certificate</%def>
<%def name="panel_icon()">${lib.icon('plus')}</%def>

<script type="text/javascript">
// Redirect back to the certs list 2 secs after clicking the browser-generate button
$(document).ready(function() {
    $('#browser-gen-commit').click(function() {
        window.setTimeout(function() {
            window.location = "${request.route_url('controls.certs')}";
        }, 2000);
    });
});
</script>

<section>
    <p><a href="${request.route_url('controls.certs')}">Go back to Certificates List</a></p>

    <div class="clearfix">
    <div class="halfsplit left">
        <%lib:secure_form>
        <h1 class="top-heading">Generate Certificate in Browser</h1>
        <dl class="standard-form">
            ${lib.field(browser_form.days)}
            ${lib.field(browser_form.pubkey)}
            <dd class="standard-form-footer">
                <button id="browser-gen-commit">Generate in Browser</button>
            </dd>
        </dl>
        </%lib:secure_form>
    </div>
    <div class="halfsplit right">
        <p>This will cause your browser to generate and install a certificate
        automatically.</p>
        <p>It is the easiest option, but it's not supported by all
        browsers.  It has been tested successfully on the latest versions of:</p>
        <ul>
            <li>Chrome</li>
            <li>Firefox</li>
            <li>Opera</li>
        </ul>
        <p>Internet Explorer (any version) will not work.  Safari has not been
        tested.</p>
        <p>After generation, you should try to export your certificate from
        your browser or operating system's certificate store.  This is useful
        as a backup and will allow you to import and use the one certificate
        on multiple computers.</p>
    </div>
    </div>

    <div class="clearfix">
    <div class="halfsplit left">
        <h1>Generate Certificate on Server</h1>
        <%lib:secure_form url="${request.route_url('controls.certs.generate_server', name=request.user.name)}">
        <dl class="standard-form">
            ${lib.field(server_form.days)}
            ${lib.field(server_form.name)}
            ${lib.field(server_form.passphrase)}
            <dd class="standard-form-footer">
                <button>Generate on Server</button>
            </dd>
        </dl>
        </%lib:secure_form>
    </div>
    <div class="halfsplit right">
        <p>This will return a PKCS12 (.p12) certificate file for download and
        manual installation.</p>
        <p>This method is compatible with any browser, but you'll have to work
        out how to install the certificate yourself.</p>
        <p>The Friendly Name and Passphrase are optional.  Specifing a
        passphrase may fix import errors on certain buggy platforms.</p>
        <p><strong>Be sure to save the file when prompted</strong> -- you will not
        be able to download the generated private key again.</p>
    </div>
    </div>

    <p><a href="${request.route_url('controls.certs')}">Go back to Certificates List</a></p>
</section>
