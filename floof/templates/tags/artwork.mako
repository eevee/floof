<%inherit file="/base.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">Artwork tagged "${c.tag}"</%def>

<h1>${title()}</h1>

${artlib.thumbnail_grid(c.gallery_view.query)}
