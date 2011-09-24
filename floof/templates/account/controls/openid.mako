<%! import wtforms.widgets %>
<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">OpenID Identity Settings</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

${lib.secure_form(request.route_url('controls.openid.add'))}
<dl class="standard-form">
    ${lib.field(add_openid_form.new_openid)}
    <dd class="standard-form-footer">
        <button>Add</button>
    </dd>
</dl>
${h.end_form()}
<br />
${lib.secure_form(request.route_url('controls.openid.remove'))}
<dl class="standard-form">
    ${lib.field(remove_openid_form.openids)}
    <dd class="standard-form-footer">
        <button>Remove</button>
    </dd>
</dl>
${h.end_form()}
