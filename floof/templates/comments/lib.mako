## Render a single comment object
<%def name="single_comment(comment)">
<div class="comment">
    <div class="author">${comment.author.display_name}</div>
    <div class="time">${comment.posted_time}</div>
    <div class="content">${comment.content}</div>
</div>
</%def>


## Render an iterable of comments, nesting appropriately as it goes
<%def name="comment_tree(comments)">
<div class="discussion">
    % for comment in comments:
    ${single_comment(comment)}
    % endfor
</div>
</%def>
