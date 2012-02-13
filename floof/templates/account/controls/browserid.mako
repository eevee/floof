<%! import wtforms.widgets %>
<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">BrowserID Identity Settings</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:public/js/browserid.js'))}
</%def>

<noscript>
    <p>It looks like you don't have Javascript enabled for this site.</p>
    <p>Unfortunately, BrowserID requires Javascript to work.</p>
</noscript>
<dl class="standard-form">
    <dt>New BrowserID</dt>
    <dd>
        <a href="#" id="browserid" title="Sign-in with BrowserID to add a new email address to this account">
            <img src="https://browserid.org/i/sign_in_blue.png" alt="Sign in to add a new identity" />
        </a>
    </dd>
</dl>
<script src="https://browserid.org/include.js" async></script>
<script type="text/javascript">
    $(browseridOnClick('#browserid', '${request.route_path("controls.browserid.add")}'));
</script>

${lib.secure_form(request.route_url('controls.browserid.remove'))}
<dl class="standard-form">
    ${lib.field(form.browserids)}
    <dd class="standard-form-footer">
        <button>Remove</button>
    </dd>
</dl>
${h.end_form()}
