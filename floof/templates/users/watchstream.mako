<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">${target_user.display_name}'s watchstream</%def>

<h1>${lib.user_link(target_user)} » Watchstream</h1>
${artlib.render_gallery_sieve(artwork)}
