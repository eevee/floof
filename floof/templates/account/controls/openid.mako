<%! import wtforms.widgets %>
<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">OpenID Identity Settings</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

${h.secure_form(url.current())}

<h2>Add a New OpenID Identity</h2>
<dl>
    ${lib.field(c.openid_form.new_openid)}
</dl>
<p>${c.openid_form.add_openid() | n}</p>

<h2>Delete Existing OpenID Identities</h2>
<dl>
% if len(c.openid_form.openids.choices) == 1:
    ${lib.field(c.openid_form.openids, disabled='disabled')}
% else:
    ${lib.field(c.openid_form.openids)}
% endif
</dl>
<p>${c.openid_form.del_openids() | n}</p>

${h.end_form()}
