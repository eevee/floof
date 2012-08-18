<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Add OAuth Client</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>

<%lib:secure_form>
    <dl class="standard-form oauth-client">
        ${lib.field(form.user)}
        ${lib.field(form.name)}
        ${lib.field(form.site_uri)}
        ${lib.field(form.type)}
        ${lib.field(form.redirect_uris, hint_text=u"one per line; the first listed is the default; Native and Mobile applications should leave this blank")}
        <dd>A client identifier and (for web server clients) a client secret
        will be generated automatically.</dd>
        <dd class="standard-form-footer">
            <button type="submit">Create</button>
        </dd>
    </dl>
</%lib:secure_form>
