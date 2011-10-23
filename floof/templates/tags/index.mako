<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Tags</%def>

<section>
<h1>
    Tags
</h1>

<ul>
% for tag in tags:
<li><a href="${request.route_url('tags.view', tag=tag)}">${tag.name}</a></li>
% endfor
</ul>
</section>
