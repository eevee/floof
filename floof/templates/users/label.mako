<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">Artwork ${c.rel} ${c.this_user.display_name}</%def>

<h1>${title()}</h1>

<p>This is art the user authored.  Or something.  XXX</p>

${artlib.render_gallery_sieve(c.gallery_sieve)}
