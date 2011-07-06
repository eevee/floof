<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">User Info</%def>
<%def name="panel_icon()">${lib.icon('user')}</%def>

<%
fields = [
        'display_name',
        'email',
        'timezone',
        ]
%>

<h2>User Info</h2>
${h.secure_form(request.path_url)}

<input type="submit" class="stylish-button" value="Update" />
<dl>
    % for f in fields:
        <% field = form[f] %>\
        <% maxlen = getattr(form, '_{0}_maxlen'.format(f), None) %>\
        % if maxlen:
            ${lib.field(field, size=maxlen, maxlength=maxlen)}
        % else:
            ${lib.field(field)}
        % endif
    % endfor
</dl>
<input type="submit" class="stylish-button" value="Update" />
${h.end_form()}
