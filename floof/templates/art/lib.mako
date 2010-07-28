<%def name="thumbnail(artwork)">
## Spits out..  a thumbnail of this artwork.  It's an <li>, so this should be
## called inside a <ul>.
<li class="thumbnail">
    <a href="${url(controller='art', action='view', id=artwork.id, title=artwork.url_title)}">
        <img src="${config['filestore'].url(artwork.hash + '.thumbnail')}" alt="">
        ${artwork.title or 'Untitled'}; ${artwork.media_type}
    </a>
</li>
</%def>
