<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">\
Comments for: ${discussion.resource.member.resource_title}\
</%def>


<h1>
    ${lib.icon('balloon-ellipsis')}
    Comments for: ${discussion.resource.member.resource_title}
</h1>
${lib.resource_summary(discussion.resource)}

% if comment:
<h1>
    ${lib.icon('balloons')}
    Parent comments
</h1>
% for ancestor in comment_ancestors:
${comments_lib.single_comment(ancestor)}
% endfor
% endif

<h1 id="comment">
    ${lib.icon('balloons-white')}
    % if comment:
    Comment thread
    % else:
    ${len(comment_descendants)} comment${'' if len(comment_descendants) == 1 else 's'}
    % endif
</h1>
${comments_lib.comment_tree(comment_descendants)}

## Only show this form if we're displaying ALL comments; otherwise it's not
## obviously attached to the current comment
% if not comment and user.can('comments.add'):
<h2>
    ${lib.icon('balloon-white')}
    Write your own
</h2>
${comments_lib.write_form(comment_form, discussion.resource)}
% endif
