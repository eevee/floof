<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Upload - Artwork</%def>

<h1>
    <img src="/icons/image--arrow.png" alt="">
    Upload
</h1>

${h.form(url.current(), multipart=True)}
<dl class="standard-form">
    ${lib.field(c.form.file)}
    ${lib.field(c.form.title, size=64, maxlength=133)}

    ## Relationship stuff
    % for field in c.form.relationship_by_for:
    <dd>
        ${field() | n}
        % if field.data == u'by':
        <img src="/icons/paint-brush.png" alt="">
        % elif field.data == u'for':
        <img src="/icons/present.png" alt="">
        % endif
        ${field.label() | n}
        ${lib.field_errors(field)}
    </dd>
    % endfor
    <dd>
        ${c.form.relationship_of() | n}
        <img src="/icons/camera.png" alt="">
        ${c.form.relationship_of.label() | n}
        ${lib.field_errors(c.form.relationship_of)}
    </dd>

    <dd><button type="submit">Upload!</button></dd>
</dl>
${h.end_form()}
