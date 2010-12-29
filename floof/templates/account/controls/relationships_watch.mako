<%inherit file="base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="panel_title()">Watch ${lib.user_link(c.target_user)}</%def>
<%def name="panel_icon()">${lib.icon(u'user--plus')}</%def>

${h.form(url.current(target_user=c.target_user.name))}
<h2>Watch...</h2>
<ul>
    <li><label>
        ${c.watch_form.watch_upload()|n}
        ${lib.stdicon('uploader')}
        Art that ${c.target_user.display_name} uploads
    </label></li>
    <li><label>
        ${c.watch_form.watch_by()|n}
        ${lib.stdicon('by')}
        Art by ${c.target_user.display_name}
    </label></li>
    <li><label>
        ${c.watch_form.watch_for()|n}
        ${lib.stdicon('for')}
        Art for ${c.target_user.display_name}
    </label></li>
    <li><label>
        ${c.watch_form.watch_of()|n}
        ${lib.stdicon('of')}
        Art of ${c.target_user.display_name}
    </label></li>
</ul>

<p><button type="submit" class="stylish-button confirm">Save</button></p>
${h.end_form()}


% if c.watch:
<h2>Or...</h2>
${h.form(url(controller='controls', action='relationships_unwatch_commit', target_user=c.target_user.name))}
<p>
    <label><input type="checkbox" name="confirm"> Unwatch ${c.target_user.display_name} entirely</label>
    <br>
    <button type="submit" class="stylish-button destroy">Yes, I'm sure!</button>
</p>
${h.end_form()}
% endif
