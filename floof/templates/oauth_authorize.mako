<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">3rd Party Access Authorization</%def>

<section>

<h1>Third Party Access Request</h1>

<p>A third party client is requesting access to your account.</p>
<p>The specifics of the requested access are listed below, along with the
claimed identity of the requesting party.</p>
<p>You are under <strong>no obligation</strong> to accept this request.
If you did not initiate this access request, you should decline it.</p>
<p>Should you later change your mind, you can revoke any granted access from
your account control panel under the "OAuth" section.</p>
<%lib:secure_form submit_url id='oauth-authorize'>
    ${form.client_id()}
    ${form.redirect_uri()}
    ${form.response_type()}
    ${form.scope()}
    ${form.state()}
    <dl class="standard-form">
        <dt>Client Name</dt>
        <dd>${client.name}</dd>
        % if client.site_uri:
            <dt>Client Website</dt>
            <dd><a href="${client.site_uri}">${client.site_uri}</a></dd>
        % endif
        <dt>Client Operator</dt>
        <dd>${lib.user_link(client.user, show_trivial_username=True)}</dd>
        <dt>Access Duration</dt>
        <dd>${period}</dd>
        <dt>Requested Access</dt>
        % if not scopes:
            <dd>No access.  Huh.</dd>
        % endif
        % for scope in scopes:
            <dd>${scope_desc[scope]}</dd>
        % endfor
        <dd class="standard-form-footer">
            ${form.accept()}
            ${form.cancel()}
        </dd>
    </dl>
</%lib:secure_form>
</section>
