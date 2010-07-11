<%inherit file="/base.mako" />

<ul>
    % for artwork in c.artwork:
    <li>
        ## XXX include title..  shared code?
        <a href="${url(controller='art', action='view', id=artwork.id)}">
            ${artwork.title or 'Untitled'}; ${artwork.media_type}
        </a>
    </li>
    % endfor
</ul>
