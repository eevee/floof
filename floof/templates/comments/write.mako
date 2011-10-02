<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">\
Commenting on: ${discussion.resource.member.resource_title}\
</%def>


<h1>
    ${lib.icon('balloon-ellipsis')}
    Commenting on: ${discussion.resource.member.resource_title}
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

<h1 id="comment">
    ${lib.icon('balloons-white')}
    Comment
</h1>
${comments_lib.single_comment(comment)}
% endif


% if h.has_permission('comments.add', request.context, request):
<% hlevel = 'h2' if comment else 'h1' %>\
<${hlevel}>
    ${lib.icon('balloon-white')}
    Reply
</${hlevel}>
${comments_lib.write_form(comment_form, discussion.resource, parent_comment=comment)}
% endif
