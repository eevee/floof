<%inherit file="/base.mako" />

<%def name="title()">${c.artwork.title or 'Untitled'}</%def>

<h1>${c.artwork.title or 'Untitled'}</h1>

<div class="artwork">
    <img src="${c.artwork_url}" alt="">
</div>

<ul>
    % for user_artwork in c.artwork.user_artwork:
    <li>${user_artwork.relationship_type} ${user_artwork.user.display_name}</li>
    % endfor
</ul>
