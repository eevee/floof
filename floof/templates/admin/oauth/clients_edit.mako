<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Edit OAuth Client</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>

<%lib:secure_form>
    <dl class="standard-form oauth-client">
        <dt>Created</dt>
        <dd>${lib.time(client.created)}</dd>
        <dt>Application Type</dt>
        <dd>${u'Web Server' if client.type == u'web' else u'Native or Mobile'}</dd>
        <dt>Client Identifier</dt>
        <dd class="identifier">${client.identifier}</dd>
        <dt>Client Secret</dt>
        % if client.auth_type == u'confidential':
            <dd class="identifier">${client.secret}</dd>
        % else:
            <dd>N/A</dd>
        % endif
        ${lib.field(form.user)}
        ${lib.field(form.name)}
        ${lib.field(form.site_uri)}
        % if client.type == u'native':
            ${lib.field(form.redirect_uris, disabled="disabled")}
        % else:
            ${lib.field(form.redirect_uris)}
        % endif
        <dd class="standard-form-footer">
            <button type="submit">Save</button>
            <a href="${request.route_url('admin.oauth.clients')}">Cancel</a>
            <a href="${request.route_url('admin.oauth.clients.delete', client=client)}" class="button destructive">Delete...</a>
        </dd>
    </dl>
</%lib:secure_form>
