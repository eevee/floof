<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">User Info</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

${h.secure_form(url.current())}
<h2>Display name</h2>
${c.display_name_form.display_name(
    size=c.display_name_form._max_length,
    maxlength=c.display_name_form._max_length
)}
${c.display_name_form.update_display_name()}

${lib.field_errors(c.display_name_form.display_name)}
${h.end_form()}
