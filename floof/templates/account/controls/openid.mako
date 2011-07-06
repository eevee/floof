<%! import wtforms.widgets %>
<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">OpenID Identity Settings</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<h2>Add a New OpenID Identity</h2>
${h.secure_form(request.route_url('controls.openid.add'))}
<dl>
    ${lib.field(add_openid_form.new_openid)}
</dl>
<p><button>Add OpenID</button></p>
${h.end_form()}

<h2>Delete Existing OpenID Identities</h2>
${h.secure_form(request.route_url('controls.openid.remove'))}
<dl>
    ${lib.field(remove_openid_form.openids)}
</dl>
<p><button>Remove selected OpenIDs</button></p>
${h.end_form()}
