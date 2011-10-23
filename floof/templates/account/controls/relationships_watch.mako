<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Watch ${target_user.display_name or target_user.name}</%def>
<%def name="panel_title()">Watch ${lib.user_link(target_user)}</%def>
<%def name="panel_icon()">${lib.icon(u'user--plus')}</%def>

${lib.secure_form(request.path_url)}
${h.tags.hidden(name=u'target_user', value=target_user.name)}
<ul>
    <li><label>
        ${watch_form.watch_upload()|n}
        ${lib.stdicon('uploader')}
        Uploads
    </label></li>
    <li><label>
        ${watch_form.watch_by()|n}
        ${lib.stdicon('by')}
        By
    </label></li>
    <li><label>
        ${watch_form.watch_for()|n}
        ${lib.stdicon('for')}
        For
    </label></li>
    <li><label>
        ${watch_form.watch_of()|n}
        ${lib.stdicon('of')}
        Of
    </label></li>
</ul>

<p><button type="submit" class="stylish-button confirm">Save</button></p>
${h.end_form()}


% if watch:
<h2>Or...</h2>
${lib.secure_form(request.route_url('controls.rels.unwatch'))}
${h.tags.hidden(name=u'target_user', value=target_user.name)}
<p>
    <label><input type="checkbox" name="confirm"> Unwatch entirely</label>
    <br>
    <button type="submit" class="stylish-button destroy">Yes, I'm sure!</button>
</p>
${h.end_form()}
% endif
