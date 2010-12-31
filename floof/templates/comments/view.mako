<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">\
Comments for: ${c.discussion.resource.member.resource_title}\
</%def>


<h1>
    ${lib.icon('balloon-ellipsis')}
    Comments for: ${c.discussion.resource.member.resource_title}
</h1>
${lib.resource_summary(c.discussion.resource)}

% if c.comment:
<h1>
    ${lib.icon('balloons')}
    Parent comments
</h1>
% for ancestor in c.comment_ancestors:
${comments_lib.single_comment(ancestor)}
% endfor
% endif

<h1 id="comment">
    ${lib.icon('balloons-white')}
    % if c.comment:
    Comment thread
    % else:
    ${len(c.comment_descendants)} comment${'' if len(c.comment_descendants) == 1 else 's'}
    % endif
</h1>
${comments_lib.comment_tree(c.comment_descendants)}

## Only show this form if we're displaying ALL comments; otherwise it's not
## obviously attached to the current comment
% if not c.comment and c.user.can('comment.write'):
<h2>
    ${lib.icon('balloon-white')}
    Write your own
</h2>
${comments_lib.write_form(c.comment_form, c.discussion.resource)}
% endif
