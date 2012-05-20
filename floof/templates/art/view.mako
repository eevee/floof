<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">${artwork.title or 'Untitled'} - Artwork</%def>
<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:public/js/vendor/jquery.ui-1.8.7.js'))}
    ${h.javascript_link(request.static_url('floof:public/js/vendor/jquery.ui.rater.js'))}
</%def>

<section class="neutral-background">
<h1>
    ${lib.icon('image')}
    ${artwork.title or 'Untitled'}
</h1>

## Ye art itself
<div class="artwork">
    <img src="${request.route_url('filestore', class_=u'artwork', key=artwork.hash)}" alt="">
</div>

## Metadata and whatever
<div class="column-container">

<section class="column-2x">
    <h1>Art</h1>
    <div class="column-container">
    <div class="column-2x">
    <dl class="standard-deflist">
        <dt>Title</dt>
        <dd>${artwork.title or 'Untitled'}</dd>
        <dt>Uploader</dt>
        <dd>
            ${lib.icon('disk')}
            ${lib.user_link(artwork.uploader)}
        </dd>

        % for user_artwork in artwork.user_artwork:
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
        <%
            if artwork.rating_score is None:
                rating_score = None
            else:
                rating_score = artwork.rating_score # XXX * config['rating_radius']
        %>\
        % if request.user.can('art.rate', request.context):
            <script type="text/javascript">
            $("div.art-rater").rater({
                rate_url: "${request.route_url('art.rate', artwork=artwork)}",
                value: ${current_rating or 'null'},
                num_ratings: ${artwork.rating_count},
                rating_sum: ${rating_score or 'null'},
                auth_token: "${request.session.get_csrf_token()}", auth_token_field: "csrf_token"})
            </script>
            <noscript>
                <div class="rater-info"><span class="rater-num-ratings">${artwork.rating_count}</span> (<span class="rater-rating-sum">${rating_score or u'—'}</span>)</div>
                <% rating_chars = [u'\u2b06', u'\u2022', u'\u2b07'] %>
                % for r in range(len(rating_chars)):
                    <%lib:secure_form url="${request.route_url('art.rate', artwork=artwork)}" class_="rater-form">
                        ${h.hidden(name="rating", value=(len(rating_chars) / 2 - r))}
                    % if current_rating == (len(rating_chars) / 2 - r):
                        ${h.submit(value=rating_chars[r], name="commit", disabled="disabled")}
                    % else:
                        ${h.submit(value=rating_chars[r], name="commit")}
                    % endif
                    </%lib:secure_form>
                % endfor
            </noscript>
        % elif request.user:
            <div class="rater-info"><span class="rater-num-ratings">${artwork.rating_count}</span> (<span class="rater-rating-sum">${rating_score or u'—'}</span>)</div>
            <div class="rater-info">You do not have permission to vote.</div>
        % else:
            <div class="rater-info"><span class="rater-num-ratings">${artwork.rating_count}</span> (<span class="rater-rating-sum">${rating_score or u'—'}</span>)</div>
            <div class="rater-info">Log in to vote!</div>
        % endif
            </div>
        </div>
    </div>

    <h1 id="tags">Tags</h1>
    <p>\
    % for tag in artwork.tag_objs:
    <a href="${request.route_url('tags.view', tag=tag)}">${tag.name}</a>\
    % endfor
    </p>

    % for perm, action, form in [ \
        ('tags.add', 'add_tags', add_tag_form), \
        ('tags.remove', 'remove_tags', remove_tag_form), \
    ]:
    % if request.user.can(perm, request.context):
    <%lib:secure_form url="${request.route_url('art.' + action, artwork=artwork)}">
    <p>
        ${form.tags.label()}:
        ${form.tags()}
        <button type="submit">Go</button>
    </p>
    </%lib:secure_form>
    ${lib.field_errors(form.tags)}
    % endif
    % endfor

    <h1>Labels</h1>
    <ul class="standard-list">
        % for label in request.user.permitted('label.view', artwork.labels):
        <li>${artlib.label(label)} (by ${lib.user_link(label.user)})</li>
        % endfor
    </ul>


    % if artwork.remark:
    <h1>Remarks</h1>
    <div class="content rich-text">${h.render_rich_text(artwork.remark)}</div>
    % endif
</section>
<section class="column">
    <h1>Stats</h1>
    <dl class="standard-deflist">
        ## XXX some of these only apply to some media types
        <dt>Filename</dt>
        <dd>${artwork.original_filename}</dd>
        <dt>Uploaded at</dt>
        <dd>${lib.time(artwork.uploaded_time)}</dd>
        <dt>File size</dt>
        <dd>${artwork.file_size}</dd>
        <dt>Dimensions</dt>
        <dd>${artwork.width} × ${artwork.height}</dd>
    </dl>
</section>
</section>
</div>


<section>
    ## Comments
    <% comments = artwork.discussion.comments %>\
    <h1>
        ${lib.icon('balloons-white')}
        ${len(comments)} comment${'' if len(comments) == 1 else 's'}
    </h1>
    ${comments_lib.comment_tree(comments)}

    % if request.user.can('comments.add', request.context):
    <section>
        <h1>
            ${lib.icon('balloon-white')}
            Write your own
        </h1>
        ${comments_lib.write_form(comment_form, artwork.resource)}
    </section>
    % endif
</section>
