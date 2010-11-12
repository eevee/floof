<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

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

% if c.user.can('write_comment'):
<% hlevel = 'h2' if c.comment else 'h1' %>\
<${hlevel}>
    ${lib.icon('balloon-white')}
    Reply
</${hlevel}>
${comments_lib.write_form(c.comment_form, parent_comment=c.comment)}
% endif
