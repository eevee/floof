<%! import wtforms.widgets %>
<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Persona Identity Settings</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<section>
    <noscript>
        <p>It looks like you don't have Javascript enabled for this site.</p>
        <p>Unfortunately, Persona requires Javascript to work.</p>
    </noscript>
    <%lib:secure_form url="${request.route_url('controls.browserid.remove')}">
    <fieldset>
        <dl>
            <dt>New Persona</dt>
            <dd>
                <a href="${request.route_url('account.login')}" class="browserid" title="Sign-in with Persona to add a new email address to this account">
                    <img src="${request.static_url('floof:assets/images/persona-signin.png')}" height="22" width="79" alt="Sign in to add a new email address identity" />
                </a>
            </dd>

            ${lib.field(form.browserids)}
        </dl>
        <footer>
            <button>Remove</button>
        </footer>
    </fieldset>
    </%lib:secure_form>
</section>
