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

<%!
    _album_icons = dict(
        private='book-brown',
        public='book-bookmark',
        gallery='photo-album-blue',
        plug='plug',
    )
%>
<%def name="album_link(album)">
## Render a link to an album.  Includes an appropriate icon.
<a href="${request.route_url('albums.artwork', album=album)}">
    ${lib.icon(_album_icons[album.encapsulation])}
    ${album.name}</a>
</%def>

<%def name="thumbnail(artwork)">
## Spits out..  a thumbnail of this artwork.  It's an <li>, so this should be
## called inside a <ul>.
<li class="thumbnail">
    <a class="thumbnail" href="${request.route_url('art.view', artwork=artwork)}">
        <img src="${request.route_url('filestore', class_=u'thumbnail', key=artwork.hash)}" alt="">
    </a>
    <div class="thumbnail-meta">
        <div class="title">
            ${lib.icon(media_icon(artwork.media_type))}
            ${artwork.title or 'Untitled'}
        </div>
        ${lib.icon('disk', alt='Uploader:')} ${lib.user_link(artwork.uploader)}
    </div>
</li>
</%def>

<%def name="thumbnail_grid(artworks)">
## Creates a grid of the above automatically
<ul class="thumbnail-grid">
    % for artwork in artworks:
    ${thumbnail(artwork)}
    % endfor
</ul>
</%def>

## Shows a bigger grid of "panels", with a bit more detail about artwork
<%def name="detailed_grid(artworks)">
<ul class="detailed-thumbnail-grid">
% for artwork in artworks:
<li class="detailed-thumbnail">
    <a class="thumbnail" href="${request.route_url('art.view', artwork=artwork)}">
        <img src="${request.route_url('filestore', class_=u'thumbnail', key=artwork.hash)}" alt="">
    </a>
    <a href="${request.route_url('art.view', artwork=artwork)}">${artwork.title}</a>
</li>
% endfor
</ul>
</%def>

## Shows a detailed table of the artwork, with more focus on details than space
## constraints
<%def name="detailed_table(artworks)">
<table class="detailed-artwork-table">
<thead>
<tr>
    <th><!-- thumbnail --></th>
    <th>Title</th>
    <th>Numbers</th>
</tr>
% for artwork in artworks:
<tr>
    <td class="-thumbnail">
        <a class="thumbnail" href="${request.route_url('art.view', artwork=artwork)}">
            <img src="${request.route_url('filestore', class_=u'thumbnail', key=artwork.hash)}" alt="">
        </a>
    </td>
    <td><a href="${request.route_url('art.view', artwork=artwork)}">${artwork.title}</a></td>
    <td>
        Comments: ${artwork.discussion.comment_count} <br>
        Ratings: ${artwork.rating_count}
    </td>
</tr>
% endfor
</table>
</%def>


###### The following is all for dealing with floof.lib.gallery.GallerySieve
## objects and the forms they create.  You probably just want to use
## render_gallery_sieve().
<%!
    DISPLAY_ICONS = dict(
        thumbnails=u'ui-scroll-pane-icon',
        succinct=u'ui-scroll-pane-detail',
        detailed=u'ui-scroll-pane-list',
    )
%>\
<%def name="render_gallery_sieve(gallery_sieve, filters_open=False)">
${gallery_sieve_form(gallery_sieve.form)}
<% pager = gallery_sieve.evaluate() %>\

% if not pager.items:
<p>Nothing found.</p>
% elif gallery_sieve.display_mode == 'thumbnails':
${thumbnail_grid(pager)}
% elif gallery_sieve.display_mode == 'succinct':
${detailed_grid(pager)}
% elif gallery_sieve.display_mode == 'detailed':
${detailed_table(pager)}
% endif

% if pager.pager_type == 'discrete':
${lib.discrete_pager(pager, temporal_column_name=gallery_sieve.temporal_column_name)}
% elif pager.pager_type == 'temporal':
${lib.temporal_pager(pager)}
% endif
</%def>

<%def name="gallery_sieve_form(form)">
<div class="art-filter">
    ${h.form(request.path_url, method='GET')}
    <div class="column-container">
    <div class="column">
        <dl class="horizontal">
            ${lib.field(form.tags)}
            ${lib.field(form.time_radius)}
            % if request.user:
            ## Don't show a user-specific field for a non-user
            ${lib.field(form.my_rating)}
            % endif

            <dd><button type="submit">Filter</button></dd>
        </dl>
    </div>
    <div class="column">
        <dl class="horizontal">
            ${lib.field(form.sort)}
            <dt>${form.display.label() | n}</dt>
            <dd>
                <ul>
                    % for field in form.display:
                    <li><label>
                        ${field() | n}
                        ${lib.icon(DISPLAY_ICONS[field.data])}
                        ${field.label.text}
                    </label></li>
                    % endfor
                </ul>
                ${lib.field_errors(form.display)}
            </dd>
        </dl>
    </div>
    </div>
    ${h.end_form()}
</div>
</%def>
