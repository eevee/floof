<%! import wtforms.widgets %>
<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">OpenID Identity Settings</%def>
<%def name="panel_icon()">${lib.icon('openid')}</%def>

<section>
    <%lib:secure_form url="${request.route_url('controls.openid.add')}">
    <fieldset>
        <dl>
            ${lib.field(add_openid_form.new_openid)}
        </dl>
        <footer>
            <button>Add</button>
        </footer>
    </fieldset>
    </%lib:secure_form>
</section>

<section>
    <%lib:secure_form url="${request.route_url('controls.openid.remove')}">
    <fieldset>
        <dl>
            ${lib.field(remove_openid_form.openids)}
        </dl>
        <footer>
            <button>Remove</button>
        </footer>
    </fieldset>
    </%lib:secure_form>
</section>
