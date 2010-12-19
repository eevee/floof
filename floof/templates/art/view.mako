<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">${c.artwork.title or 'Untitled'} - Artwork</%def>

<h1>
    ${lib.icon('image')}
    ${c.artwork.title or 'Untitled'}
</h1>

## Ye art itself
<div class="artwork">
    <img src="${c.artwork_url}" alt="">
</div>

## Metadata and whatever
<div class="column-container">
<div class="column-2x">
    <h2>Art</h2>
    <dl class="standard-form">
        <dt>Title</dt>
        <dd>${c.artwork.title or 'Untitled'}</dd>
        <dt>Uploader</dt>
        <dd>
            ${lib.icon('disk')}
            ${lib.user_link(c.artwork.uploader)}
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
            ${lib.user_link(user_artwork.user)}
        </dd>
        % endfor
    </dl>

    <h2 id="tags">Tags</h2>
    <p>\
    % for tag in c.artwork.tags:
    <a href="${url(controller='tags', action='view', name=tag)}">${tag}</a>\
    % endfor
    </p>

    % for perm, action, form in [ \
        ('add_tags', 'add_tags', c.add_tag_form), \
        ('remove_tags', 'remove_tags', c.remove_tag_form), \
    ]:
    % if c.user.can(perm):
    ${h.form(url(controller='art', action=action, id=c.artwork.id))}
    <p>
        ${form.tags.label()}:
        ${form.tags()}
        <button type="submit">Go</button>
    </p>
    ${h.end_form()}
    ${lib.field_errors(form.tags)}
    % endif
    % endfor
</div>
<div class="column">
    <h2>Stats</h2>
    <dl class="standard-form">
        ## XXX some of these only apply to some media types
        <dt>Filename</dt>
        <dd>${c.artwork.original_filename}</dd>
        <dt>Uploaded at</dt>
        <dd>${lib.time(c.artwork.uploaded_time)}</dd>
        <dt>File size</dt>
        <dd>${c.artwork.file_size}</dd>
        <dt>Dimensions</dt>
        <dd>${c.artwork.width} × ${c.artwork.height}</dd>
    </dl>
</div>
</div>

## Comments
<% comments = c.artwork.discussion.comments %>\
<h1>
    ${lib.icon('balloons-white')}
    ${len(comments)} comment${'' if len(comments) == 1 else 's'}
</h1>
${comments_lib.comment_tree(comments)}

% if c.user.can('write_comment'):
<h2>
    ${lib.icon('balloon-white')}
    Write your own
</h2>
${comments_lib.write_form(c.comment_form, c.artwork.resource)}
% endif
