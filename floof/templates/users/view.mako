<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${target_user.display_name}</%def>

<h1>
    ${lib.icon('user-nude')} <a href="${request.route_url('users.profile', user=target_user)}">${target_user.name}</a>
    % if target_user.display_name is not None:
    (${target_user.display_name})
    % endif
</h1>

## this is kinda grody until there are enough bits to flesh it out
% if request.user != target_user:
<div>
    <a href="${h.update_params(request.route_url('controls.rels.watch'), target_user=target_user.name)}">
        % if any(watch.other_user == target_user for watch in request.user.watches):
        ${lib.icon(u'user--pencil')} Modify watch
        % else:
        ${lib.icon(u'user--plus')} Watch
        % endif
    </a>
</div>
<hr>
% endif

% for rel in user_artwork_types:
<%
    art_pager = related_art[rel].evaluate()
    if not art_pager.items:
        continue
%>
<h2>Art ${rel} ${target_user.display_name or target_user.name}</h2>
${artlib.thumbnail_grid(art_pager)}
% endfor
