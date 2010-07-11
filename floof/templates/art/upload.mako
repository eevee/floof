<%inherit file="/base.mako" />

<%def name="title()">Upload art</%def>

<h1>Upload</h1>

${h.form(url.current(), multipart=True)}
<dl class="standard-form">
    <dd>
        ${c.form.file() | n}
        ${c.form.errors}
    </dd>

    <dd><button type="submit">Upload!</button></dd>
</dl>
${h.end_form()}
