<%namespace name="lib" file="/lib.mako" />

## Render a single comment object
<%def name="single_comment(comment, indent=0)">
<div class="comment" style="margin-left: ${indent * 2}em;" id="comment-${comment.id}">
    <div class="avatar">(avatar)</div>
    <div class="header">
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
    indent = 0
    right_ancestry = []
%>\

    % for comment in comments:
    <%
        # Indent by checking the current comment's left endpoint against
        # potential parents' right endpoints.  If our left is less than their
        # right, then this comment is still a descendent.

        # If this comment is a child of the last, indent by a level
        if last_comment and comment.left < last_comment.right:
            indent += 1
            # Remember current ancestory relevant to the root
            right_ancestry.append(last_comment)

        # Conversely, for every ancestor we just escaped, unindent by a level
        while right_ancestry and comment.left > right_ancestry[-1].right:
            indent -= 1
            right_ancestry.pop()

        last_comment = comment
    %>\

    ${single_comment(comment, indent=indent)}
    % endfor
</div>
</%def>
