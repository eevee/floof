<%namespace name="lib" file="/lib.mako" />

<%!
def media_icon(type):
    """Determine the icon that should be used for an artwork.

    Add more elifs as necessary.
    """
    if type == "image":
        return 'image'
    elif type == "music":
        return 'music-beam'
    else:
        return 'question'
%>

<%def name="thumbnail(artwork)">
## Spits out..  a thumbnail of this artwork.  It's an <li>, so this should be
## called inside a <ul>.
<li class="thumbnail">
    <a class="thumbnail" href="${h.art_url(artwork)}">
        <img src="${url('filestore', key=artwork.hash + '.thumbnail')}" alt="">
    </a>
    <div class="thumbnail-meta">
        <div class="title">
            ${lib.icon(media_icon(artwork.media_type))}
            ${artwork.title or 'Untitled'}
        </div>
        ${lib.icon('disk', alt='Uploader:')} ${lib.user(artwork.uploader)}
    </div>
</li>
</%def>
