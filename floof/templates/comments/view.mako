<%inherit file="/base.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<h1>Parent comments</h1>
% for ancestor in c.comment_ancestry:
${comments_lib.single_comment(ancestor)}
% endfor

<h1>Comment thread</h1>
${comments_lib.comment_tree(c.comment_subtree)}
