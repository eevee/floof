<%namespace name="lib" file="/lib.mako" />

## Render a single comment object
<%def name="single_comment(comment)">
<div class="comment" id="comment-${comment.id}">
    <div class="avatar">(avatar)</div>
    <div class="header">
        <ul class="links">
            <li><a href="${url(controller='comments', action='write', subcontroller='art', comment_id=comment.id, id=c.artwork.id, title='foo', anchor="comment")}">Reply</a></li>
            <li><a href="${url(controller='comments', action='view', subcontroller='art', comment_id=comment.id, id=c.artwork.id, title='foo', anchor="comment")}">Link</a></li>
        </ul>
        ${lib.user_link(comment.author)}
        at ${lib.time(comment.posted_time)}
    </div>
    <div class="content">${comment.content}</div>
</div>
</%def>


## Render an iterable of comments, nesting appropriately as it goes
<%def name="comment_tree(comments)">
<div class="discussion">
<%
    last_comment = None
    right_ancestry = []
%>\

    % for comment in comments:
    <%
        # Indent by checking the current comment's left endpoint against
        # potential parents' right endpoints.  If our left is less than their
        # right, then this comment is still a descendent.

        # If this comment is a child of the last, indent by a level
        if last_comment and comment.left < last_comment.right:
            context.write('<div class="comment-child">\n')
            # Remember current ancestory relevant to the root
            right_ancestry.append(last_comment)

        # Conversely, for every ancestor we just escaped, unindent by a level
        while right_ancestry and comment.left > right_ancestry[-1].right:
            context.write('</div>\n')
            right_ancestry.pop()

        last_comment = comment
    %>\

    ${single_comment(comment)}
    % endfor

    % for still_open_container in right_ancestry:
    </div>
    % endfor
</div>
</%def>

<%def name="write_form(form, parent_comment=None)">
<%
    comment_kwarg = dict()
    if parent_comment:
        comment_kwarg['comment_id'] = parent_comment.id
%>\
${h.form(url(controller='comments', action='write_commit', subcontroller='art', id=c.artwork.id, title='foo', **comment_kwarg), method='POST')}
<p>${form.message(rows=25, cols=80)}</p>
<p>
    <button type="submit">POST TO INTERNET</button>
</p>
${h.end_form()}
</%def>
