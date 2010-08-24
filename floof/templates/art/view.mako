<%inherit file="/base.mako" />

<%def name="title()">${c.artwork.title or 'Untitled'} - Artwork</%def>

<h1>
    <img src="/icons/image.png" alt="">
    ${c.artwork.title or 'Untitled'}
</h1>

<div class="artwork">
    <img src="${c.artwork_url}" alt="">
</div>

<div class="column-container">
<div class="column-2x">
    <h2>Art</h2>
    <dl class="standard-form">
        <dt>Title</dt>
        <dd>${c.artwork.title or 'Untitled'}</dd>
        <dt>Uploader</dt>
        <dd>
            <img src="/icons/disk.png" alt="">
            ${c.artwork.uploader.display_name}
        </dd>

        % for user_artwork in c.artwork.user_artwork:
        <dt>${user_artwork.relationship_type}</dt>
        <dd>
            % if user_artwork.relationship_type == u'by':
            <img src="/icons/paint-brush.png" alt="">
            % elif user_artwork.relationship_type == u'for':
            <img src="/icons/present.png" alt="">
            % elif user_artwork.relationship_type == u'of':
            <img src="/icons/camera.png" alt="">
            % endif
            ${user_artwork.user.display_name}
        </dd>
        % endfor
    </dl>
</div>
<div class="column">
    <h2>Stats</h2>
    <dl class="standard-form">
        ## XXX some of these only apply to some media types
        <dt>Filename</dt>
        <dd>${c.artwork.original_filename}</dd>
        <dt>File size</dt>
        <dd>${c.artwork.file_size}</dd>
        <dt>Dimensions</dt>
        <dd>${c.artwork.width} × ${c.artwork.height}</dd>
    </dl>
</div>
</div>
