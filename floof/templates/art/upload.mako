<%inherit file="/base.mako" />

<%def name="title()">Upload art</%def>

<h1>Upload</h1>

${h.form(url.current(), multipart=True)}
<dl class="standard-form">
    ${c.form.errors}

    <dd>
        ${c.form.file() | n}
    </dd>
    <dd>
        ${c.form.title(size=64, maxlength=133) | n}
    </dd>

    <dd>
        ${c.form.relationship_by_for() | n}
    </dd>
    <dd>
        ${c.form.relationship_of() | n}
        ${c.form.relationship_of.label() | n}
    </dd>

    <dd><button type="submit">Upload!</button></dd>
</dl>
${h.end_form()}
