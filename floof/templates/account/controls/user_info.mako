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

<h1>General</h1>
${lib.secure_form(request.path_url)}
<dl class="standard-form">
    % for f in fields:
        <% field = form[f] %>\
        <% maxlen = getattr(form, '_{0}_maxlen'.format(f), None) %>\
        % if maxlen:
            ${lib.field(field, size=maxlen, maxlength=maxlen)}
        % else:
            ${lib.field(field)}
        % endif
    % endfor
    <dd class="standard-form-footer">
        <button>Update</button>
    </dd>
</dl>
${h.end_form()}

<h1>Avatar</h1>
<dl class="standard-form">
    <dt>Current Avatar</dt>
    <dd>
        ${lib.avatar(request, request.user)}
        <p><a href="${request.route_url('controls.avatar')}">Change...</a></p>
    </dd>
</dl>
