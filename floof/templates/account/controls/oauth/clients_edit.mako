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
        ${lib.field(form.name, hint_text=u"will appear in the authorization UI")}
        ${lib.field(form.site_uri, hint_text=u"will appear in the authorization UI; should be a web page explaining your application to other users")}
        % if client.type == u'native':
            ${lib.field(form.redirect_uris, disabled="disabled", hint_text=u"native applications may only have authorization codes directed to the browser screen (using the 'urn:' URI) or to a URI with scheme 'http' or 'https' and authority 'localhost' (with any port)")}
        % else:
            ${lib.field(form.redirect_uris, hint_text=u"URIs to which authorization codes may be directed, one per line; the first listed is the default")}
        % endif
        <dd class="standard-form-footer">
            <button type="submit">Save</button>
            <a href="${request.route_url('controls.oauth')}" class="button">Cancel</a>
            <a href="${request.route_url('controls.oauth.clients.delete', client=client)}" class="button destructive">Delete...</a>
        </dd>
    </dl>
</%lib:secure_form>
