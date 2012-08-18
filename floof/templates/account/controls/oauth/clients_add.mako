<%inherit file="../base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Add OAuth Client</%def>
<%def name="panel_icon()">${lib.icon('oauth-small')}</%def>

<%lib:secure_form>
    <dl class="standard-form oauth-client">
        ${lib.field(form.name, hint_text=u"will appear in the authorization UI; a separate client identifier for programmatic use will be generated automatically")}
        ${lib.field(form.site_uri, hint_text=u"will appear in the authorization UI; should be a web page explaining your application to other users")}
        ${lib.field(form.type, hint_text=u"web server applications will be issued with a client secret")}
        ${lib.field(form.redirect_uris, hint_text=u"URIs to which authorization codes may be directed, one per line; the first listed is the default; Native and Mobile applications should leave this blank")}
        <dd>A client identifier and (for web server clients) a client secret
        will be generated automatically.</dd>
        <dd class="standard-form-footer">
            <button type="submit">Create</button>
        </dd>
    </dl>
</%lib:secure_form>
