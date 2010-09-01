<%def name="thumbnail(artwork)">
## Spits out..  a thumbnail of this artwork.  It's an <li>, so this should be
## called inside a <ul>.
<li class="thumbnail">
    <a href="${h.art_url(artwork)}">
        <img src="${config['filestore'].url(artwork.hash + '.thumbnail')}" alt="">
    </a>
    <div class="thumbnail-meta">
        ${artwork.title or 'Untitled'}; ${artwork.media_type}
    </div>
</li>
</%def>
