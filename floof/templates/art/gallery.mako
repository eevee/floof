<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">Artwork</%def>

<section>
<h1>${title()}</h1>

<div class="artwork-categories">
    ${h.form(request.path_url, method='GET', class_='inline')}
        Browse:
        <span class="btn-set">
        <button class="stylish-button selected" disabled="disabled">Everything</button>
        ## FILTERS: time < 24h.  not mine?  SORT: rating, desc
        <button class="stylish-button">Popular today</button>
        ## FILTERS: time < 24h.  not mine?  SORT: number of ratings today?, desc
        <button class="stylish-button">Suddenly, attention</button>
        ## FILTERS: time < 12h?  #ratings < X?  SORT: #ratings asc?
        <button class="stylish-button">Up and coming</button>
        ## FILTERS: not mine?  SORT: rating-to-me
        <button class="stylish-button">Art I might like</button>
        </span>
    ${h.end_form()}
</div>

${artlib.render_gallery_sieve(gallery_sieve)}
</section>
