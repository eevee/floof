<%inherit file="/base.mako" />

<%def name="title()">${http_status}</%def>

<section>
    <h1>${http_status}</h1>

    <p>${message}</p>
</section>
