<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">${c.artwork.title or 'Untitled'} - Artwork</%def>

<h1>
    ${lib.icon('image')}
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
            ${lib.icon('disk')}
            ${c.artwork.uploader.display_name}
        </dd>

        % for user_artwork in c.artwork.user_artwork:
        <dt>${user_artwork.relationship_type}</dt>
        <dd>
            % if user_artwork.relationship_type == u'by':
            ${lib.icon('paint-brush')}
            % elif user_artwork.relationship_type == u'for':
            ${lib.icon('present')}
            % elif user_artwork.relationship_type == u'of':
            ${lib.icon('camera')}
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
        <dt>Uploaded at</dt>
        <dd>${c.user.localtime(c.artwork.uploaded_time).strftime('%A, %d %B %Y at %H:%M %Z')}</dd>
        <dt>File size</dt>
        <dd>${c.artwork.file_size}</dd>
        <dt>Dimensions</dt>
        <dd>${c.artwork.width} × ${c.artwork.height}</dd>
    </dl>
</div>
</div>
