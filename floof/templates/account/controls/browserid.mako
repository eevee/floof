<%! import wtforms.widgets %>
<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">BrowserID Identity Settings</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<section>
    <noscript>
        <p>It looks like you don't have Javascript enabled for this site.</p>
        <p>Unfortunately, BrowserID requires Javascript to work.</p>
    </noscript>
    <dl class="standard-form">
        <dt>New BrowserID</dt>
        <dd>
            <a href="${request.route_url('account.login')}" class="browserid" title="Sign-in with BrowserID to add a new email address to this account">
                <img src="https://browserid.org/i/sign_in_blue.png" height="22" width="79" alt="Sign in to add a new email address identity" />
            </a>
        </dd>
    </dl>

    <%lib:secure_form url="${request.route_url('controls.browserid.remove')}">
    <dl class="standard-form">
        ${lib.field(form.browserids)}
        <dd class="standard-form-footer">
            <button>Remove</button>
        </dd>
    </dl>
    </%lib:secure_form>
</section>
