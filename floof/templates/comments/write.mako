<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">\
Commenting on: ${c.discussion.resource.member.resource_title}\
</%def>


<h1>
    ${lib.icon('balloon-ellipsis')}
    Commenting on: ${c.discussion.resource.member.resource_title}
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

<h1 id="comment">
    ${lib.icon('balloons-white')}
    Comment
</h1>
${comments_lib.single_comment(c.comment)}
% endif


% if c.user.can('comments.add'):
<% hlevel = 'h2' if c.comment else 'h1' %>\
<${hlevel}>
    ${lib.icon('balloon-white')}
    Reply
</${hlevel}>
${comments_lib.write_form(c.comment_form, c.discussion.resource, parent_comment=c.comment)}
% endif
