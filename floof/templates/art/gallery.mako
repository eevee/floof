<%inherit file="/base.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<ul class="thumbnail-grid">
    % for artwork in c.artwork:
    ${artlib.thumbnail(artwork)}
    % endfor
</ul>
