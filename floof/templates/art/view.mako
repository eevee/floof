<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">${artwork.title or 'Untitled'} - Artwork</%def>
<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:assets/js/vendor/jquery.ui-1.8.7.js'))}
    ${h.javascript_link(request.static_url('floof:assets/js/widget/rater.js'))}
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

        <dt>Artist</dt>
        % for user_artwork in artwork.user_artwork:
        <dd>
            ${lib.icon('paint-brush')}
            ${lib.user_link(user_artwork.user)}
        </dd>
        % endfor
    </dl>

    </div>
## Rating
    <div class="column">
        <div class="art-rater">
        <%
            rating_score = None
            if request.user.show_art_scores and request.user.can('art.view_score'):
                rating_score = '{0:.3f}'.format(artwork.rating_score) # XXX * config['rating_radius']
        %>\
        % if request.user.can('art.rate', request.context):
            <script type="text/javascript">
            $("div.art-rater").rater({
                rate_url: "${request.route_url('art.rate', artwork=artwork)}",
                value: ${current_rating if current_rating is not None else 'null'},
                num_ratings: ${artwork.rating_count},
                rating_score: ${'"' + rating_score + '"' if rating_score is not None else 'null' | n}});
            </script>
            <noscript>
                <div class="rater-info">
                    <p class="rater-num-ratings">${artwork.rating_count}</p>
                    % if rating_score is not None:
                        <p class="rater-rating-score">(${rating_score})</p>
                    % endif
                </div>
                <% rating_opts = [(1, u'\u2b06'), (0, u'\u2022'), (-1, u'\u2b07')] %>
                % for rating, sigil in rating_opts:
                    <%lib:secure_form url="${request.route_url('art.rate', artwork=artwork)}" class_="rater-form">
                        ${h.hidden(name="rating", value=rating)}
                    % if current_rating == rating:
                        ${h.submit(value=sigil, name="commit", disabled="disabled")}
                    % else:
                        ${h.submit(value=sigil, name="commit")}
                    % endif
                    </%lib:secure_form>
                % endfor
            </noscript>
        % else:
            <div class="rater-info">
                <p class="rater-num-ratings">${artwork.rating_count}</p>
                % if rating_score is not None:
                    <p class="rater-rating-score">(${rating_score})</p>
                % endif
            </div>
            % if request.user == artwork.uploader:
                <p>You uploaded this artwork.</p>
            % elif request.user:
                <p>You do not have permission to vote.</p>
            % endif
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

    <h1>Albums</h1>
    <ul class="standard-list">
        ## TODO artist
        % for album in request.user.permitted('album.view', artwork.albums):
        <li>${artlib.album_link(album)} (${lib.user_link(album.user)}'s)</li>
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
