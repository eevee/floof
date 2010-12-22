<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${c.this_user.display_name}</%def>

<h1>${lib.icon('user-nude')} <a href="${url.current(action='profile')}">${c.this_user.name}</a></h1>

## this is kinda grody until there are enough bits to flesh it out
% if c.user != c.this_user:
${h.form(url(controller='controls', action='relationships'))}
<div>
    <button class="stylish-button">Watch art</button>
</div>
${h.end_form()}
% endif
<hr>

% for rel in c.user_artwork_types:
<%
    arts = c.related_art[rel].get_query().all()
    if not arts:
        continue
%>
<h2>Art ${rel} ${c.this_user.name}</h2>
${artlib.thumbnail_grid(arts)}
% endfor
