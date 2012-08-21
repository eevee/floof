<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Revoke OAuth Authorization</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>

<p>Are you sure you wish to revoke this OAuth access authorization?</p>

<%lib:secure_form>
    <dl class="standard-form oauth-client">
        <dt>Client Name</dt>
        <dd>${authz.client.name}</dd>
        % if authz.client.site_uri:
            <dt>Site URL</dt>
            <dd class="identifier">${authz.client.site_uri}</dd>
        % endif
        <dt>Scopes</dt>
        % if authz.scope_objs:
            % for scope in authz.scope_objs:
                <dd>${scope.description}</dd>
            % endfor
        % else:
            <dd>&lt;None&gt;</dd>
        % endif
        <dt>Created</dt>
        <dd>${lib.time(authz.created)}</dd>
        <dd class="standard-form-footer">
            <button type="submit" class="destructive">Confirm Revocation</button>
            <a class="button" href="${request.route_url('controls.oauth')}">Cancel</a>
        </dd>
    </dl>
</%lib:secure_form>
