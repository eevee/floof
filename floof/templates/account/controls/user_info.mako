<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">User Info</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<%
fields = [
        'display_name',
        'timezone',
        ]
%>

${h.secure_form(url.current())}
% for f in fields:
    <% field = getattr(c.form, f) %>
    <% maxlen = getattr(c.form, '_{0}_maxlen'.format(f), None) %>
    <h2>${field.label}</h2>
    % if maxlen:
        ${field(size=maxlen, maxlength=maxlen)}
    % else:
        ${field()}
    % endif
    ${c.form.update()}
    ${lib.field_errors(field)}
% endfor
${h.end_form()}
