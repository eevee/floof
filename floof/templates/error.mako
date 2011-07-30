<%inherit file="/base.mako" />

<%def name="title()">${http_status}</%def>

<h1>${http_status}</h1>

<p>${message}</p>
