<%inherit file="/base.mako" />

<%def name="title()">Tags</%def>

<ul>
% for tag in tags:
<li><a href="${request.route_url('tags.view', tag=tag)}">${tag.name}</a></li>
% endfor
</ul>

