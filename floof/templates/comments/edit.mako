<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">\
Editing comment from: ${discussion.resource.member.resource_title}\
</%def>

<section>
<h1>
    ${lib.icon('balloon-ellipsis')}
    Editing comment from: ${discussion.resource.member.resource_title}
</h1>
${lib.resource_summary(discussion.resource)}


<h2>
    ${lib.icon('balloons')}
    Parent comments
</h2>
% for ancestor in comment_ancestors:
${comments_lib.single_comment(ancestor)}
% endfor

<h2>
    ${lib.icon('balloon-white')}
    Edit comment
</h2>
${comments_lib.edit_form(comment_form, discussion.resource, comment)}
</section>
