<%inherit file="/base.mako" />

<%def name="title()">${c.artwork.title or 'Untitled'}</%def>

<h1>${c.artwork.title or 'Untitled'}</h1>

<p><img src="${c.artwork_url}" alt=""></p>
