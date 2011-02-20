<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />

<%def name="title()">Artwork</%def>

<h1>${title()}</h1>

    ${h.form(url.current(), method='GET', class_='inline')}
        ## FILTERS: time < 24h.  not mine?  SORT: rating, desc
        <button class="stylish-button selected" disabled="disabled">Everything</button>
        ## FILTERS: time < 24h.  not mine?  SORT: rating, desc
        <button class="stylish-button">Popular today</button>
        ## FILTERS: time < 12h?  #ratings < X?  SORT: #ratings asc?
        <button class="stylish-button">Up and coming</button>
        ## FILTERS: not mine?  SORT: rating-to-me
        <button class="stylish-button">Art I might like</button>
    ${h.end_form()}


<%
    DISPLAY_ICONS = dict(
        thumbnails=u'ui-scroll-pane-icon',
        succinct=u'ui-scroll-pane-detail',
        detailed=u'ui-scroll-pane-list',
    )
%>\
<div class="art-filter">

${h.form(url.current(), method='GET')}
<div class="column-container">
<div class="column">
    <dl class="standard-form">
        ${lib.field(c.form.tags)}
        ${lib.field(c.form.time_radius)}
        ${lib.field(c.form.my_rating)}

        <dd><button type="submit">Update</button></dd>
    </dl>
</div>
<div class="column">
    <dl class="standard-form">
        ${lib.field(c.form.sort)}
        <dt>${c.form.display.label() | n}</dt>
        <dd>
            <ul>
                % for field in c.form.display:
                <li><label>
                    ${field() | n}
                    ${lib.icon(DISPLAY_ICONS[field.data])}
                    ${field.label.text}
                </label></li>
                % endfor
            </ul>
            ${lib.field_errors(c.form.display)}
        </dd>
    </dl>
</div>
</div>
${h.end_form()}

</div>

${artlib.thumbnail_grid(c.gallery_view.get_query())}
