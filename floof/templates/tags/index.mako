<%inherit file="/base.mako" />

<%def name="title()">Tags</%def>

<ul>
% for tag in tags:
<li><a href="${request.route_url('tags.view', name=tag.name)}">${tag.name}</a></li>
% endfor
</ul>

