<%inherit file="/base.mako"/>

<%def name="title()">Tag "${tag.name}"</%def>

<section>
<h1>${title()}</h1>

<p><a href="${request.route_url('tags.artwork', tag=tag)}">View art with this tag.</a></p>
<p>Stat porn goes here.</p>

<dl class="standard-form">
<dt><span title="# of arts tagged with this tag">Tagged</span></dt>
<dd><a href="${request.route_url('tags.artwork', tag=tag)}">${len(tag.artwork)}</a></dd>

<dt><span title="# of users watching this tag">Watching</span></dt>
<dd>???</dd>

<dt><span title="# of users ignoring this tag">Ignoring</span></dt>
<dd>???</dd>

<dt><span title="Average rating of art tagged with with tag">Average rating</span></dt>
<dd>???</dd>

<dt>etc.</dt>
</dl>

<h2>Similar tags</h2>

<p>???</p>

<h2>Usage over time.</h2>

<p>???</p>

</section>
