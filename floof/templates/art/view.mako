<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">${c.artwork.title or 'Untitled'} - Artwork</%def>
<%def name="script_dependencies()">
    ${h.javascript_link('/js/lib/jquery.ui-1.8.7.js')}
    ${h.javascript_link('/js/lib/jquery.ui.rater.js')}
</%def>

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
    <div class="column-container">
    <div class="column-2x">
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

    </div>
## Rating
    <div class="column">
        <div class="art-rater">
        % if c.user.can('art.rate'):
            <script type="text/javascript">
            $("div.art-rater").rater({
                rate_url: "${url(controller='art', action='rate', id=c.artwork.id)}",
                value: ${c.current_rating},
                num_ratings: ${c.artwork.rating_count},
                rating_sum: ${'null' if c.artwork.rating_score is None else c.artwork.rating_score * config['rating_radius']},
                auth_token: "${h.authentication_token()}", auth_token_field: "${h.token_key}"})
            </script>
            <noscript>
                <div class="rater-info"><span class="rater-num-ratings">${c.artwork.rating_count}</span> (<span class="rater-rating-sum">${c.artwork.rating_score * config['rating_radius']}</span>)</div>
                <% rating_chars = [u'\u2b06', u'\u2022', u'\u2b07'] %>
                % for r in range(len(rating_chars)):
                    ${h.secure_form(url(controller='art', action='rate', id=c.artwork.id), class_="rater-form")}
                        ${h.hidden(name="rating", value=(len(rating_chars) / 2 - r))}
                    % if c.current_rating == (len(rating_chars) / 2 - r):
                        ${h.submit(value=rating_chars[r], name="commit", disabled="disabled")}
                    % else:
                        ${h.submit(value=rating_chars[r], name="commit")}
                    % endif
                    ${h.end_form()}
                % endfor
            </noscript>
        % elif c.user:
            <div class="rater-info"><span class="rater-num-ratings">${c.artwork.rating_count}</span> (<span class="rater-rating-sum">${c.artwork.rating_score * config['rating_radius']}</span>)</div>
            <div class="rater-info">You do not have permission to vote.</div>
        % else:
            <div class="rater-info"><span class="rater-num-ratings">${c.artwork.rating_count}</span> (<span class="rater-rating-sum">${c.artwork.rating_score * config['rating_radius']}</span>)</div>
            <div class="rater-info">Log in to vote!</div>
        % endif
            </div>
        </div>
    </div>
    <h2 id="tags">Tags</h2>
    <p>\
    % for tag in c.artwork.tags:
    <a href="${url(controller='tags', action='view', name=tag)}">${tag}</a>\
    % endfor
    </p>

    % for perm, action, form in [ \
        ('tags.add', 'add_tags', c.add_tag_form), \
        ('tags.remove', 'remove_tags', c.remove_tag_form), \
    ]:
    % if c.user.can(perm):
    ${h.secure_form(url(controller='art', action=action, id=c.artwork.id))}
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

% if c.user.can('comments.add'):
<h2>
    ${lib.icon('balloon-white')}
    Write your own
</h2>
${comments_lib.write_form(c.comment_form, c.artwork.resource)}
% endif
