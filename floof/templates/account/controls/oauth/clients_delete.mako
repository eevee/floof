<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Delete OAuth Client</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>

<p>Are you super sure you wish to delete this OAuth client?</p>

% if client.refresh_tokens:
  <p><strong>All ${len(client.refresh_tokens)} persistent authorizations
  (refresh tokens) will be <em>permanently lost</em>.</strong></p>
% endif

<%lib:secure_form>
    <dl class="standard-form oauth-client">
        <dt>Client Name</dt>
        <dd class="identifier">${client.name}</dd>
        % if client.site_uri:
            <dt>Site URL</dt>
            <dd class="identifier">${client.site_uri}</dd>
        % endif
        <dt>Application Type</dt>
        <dd>${u'Web Server' if client.type == u'web' else u'Native or Mobile'}</dd>
        <dt>Client ID</dt>
        <dd class="identifier">${client.identifier}</dd>
        <dt>Created</dt>
        <dd>${lib.time(client.created)}</dd>
        <dd class="standard-form-footer">
            <button type="submit" class="destructive">Confirm Deletion</button>
            <a class="button" href="${request.route_url('controls.oauth')}">Cancel</a>
        </dd>
    </dl>
</%lib:secure_form>
