<%inherit file="/base.mako" />

<%def name="title()">Tags</%def>

<ul>
% for tag in c.tags:
<li><a href="${url(controller='tags', action='view', name=tag.name)}">${tag.name}</a></li>
% endfor
</ul>

