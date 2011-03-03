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


% if pager.items:
${thumbnail_grid(pager)}
% else:
<p>Nothing found.</p>
% endif

##% if pager.skip:
##<p>Showing from ${lib.time(pager.skip)}...</p>
##% endif
% if pager.items and pager.item_count:
<p>
    % if pager.item_count > pager.skip + 1:
    ${pager.skip + 1}–${min(pager.skip + pager.page_size, pager.item_count)}
    % else:
    ${pager.item_count}
    % endif
    of ${pager.item_count}
</p>
% elif pager.items:
<p>
    ${pager.skip + 1}–${pager.skip + pager.page_size} of some number...
</p>
% endif
% for page in pager.pages():
% if page is None:
<li>…</li>
% elif page == pager.current_page:
<li>
    % if page == int(page):
    ${int(page + 1)}
    % else:
    ${int(page + 1)}½
    % endif
</li>
% else:
<li><a href="${url.current(**dict(pager.formdata.items() + [('skip', page * pager.page_size)]))}">${page + 1}</a></li>
% endif
% endfor
</%def>

<%def name="gallery_sieve_form(form)">
<div class="art-filter">
    ${h.form(url.current(), method='GET')}
    <div class="column-container">
    <div class="column">
        <dl class="standard-form">
            ${lib.field(form.tags)}
            ${lib.field(form.time_radius)}
            ${lib.field(form.my_rating)}

            <dd><button type="submit">Filter</button></dd>
        </dl>
    </div>
    <div class="column">
        <dl class="standard-form">
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
