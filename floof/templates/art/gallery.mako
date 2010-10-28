<%inherit file="/base.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">
Artwork
% if c.relation:
${c.relation} ${c.related_user.name}
% elif c.tag:
tagged "${c.tag}"
% endif
</%def>

% if c.tag:
<h1>${title()}</h1>
% endif

<ul class="thumbnail-grid">
    % for artwork in c.artwork:
    ${artlib.thumbnail(artwork)}
    % endfor
</ul>
