<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Authentication Options</%def>
<%def name="panel_icon()">${lib.icon('key')}</%def>

<section>
    <p>${lib.icon('exclamation', 'Warning!')}
    This control is intended for use by <strong>advanced users</strong> only.</p>

    <%lib:secure_form>
    <fieldset>
        <dl>
            ${lib.field(form.cert_auth)}
        </dl>
        <footer>
            <button>Update</button>
        </footer>
    </fieldset>
    </%lib:secure_form>

    <p>There are important things to be aware of when choosing any non-default
    option.  Some of them are listed below.</p>
    <ol class="standard-list">
        <li>If you choose one of these Authentication Options and log in with
        just a certificate, it will not be possible to log out using the site's
        web interface.  You will have to know how to get your web browser to
        stop authenticating with the certificate.</li>

        <li>If you choose to require certificates for login or for sensitive
        operations and subsequently all certificates registered against your
        account expire or are revoked, you will automatically be able to log
        in and perform sensitive operations with just your OpenID or Persona.
        That is, your Certificate Authentication Option will be automatically
        changed to &quot;Allow for login&quot;.</li>

        <li>Options that require certificates will be hidden until you select
        &quot;Allow for login&quot; and authenticate with a certificate.</l1>
    </ol>
</section>
