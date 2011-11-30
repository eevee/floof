<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Upload - Artwork</%def>

<section>
<h1>
    ${lib.icon('image--arrow')}
    Upload
</h1>

${lib.secure_form(request.path_url, multipart=True)}
<dl class="standard-form">
    ${lib.field(form.file)}
    ${lib.field(form.title, size=64, maxlength=133)}
    ${lib.field(form.tags, size=64)}

    ## Relationship stuff
    % for field in form.relationship:
    <dd>
        ${field() | n}
        % if field.data == u'by':
        ${lib.icon('paint-brush')}
        % elif field.data == u'for':
        ${lib.icon('present')}
        % elif field.data == b'of':
        ${lib.icon('camera')}
        % endif
        ${field.label() | n}
    </dd>
    % endfor
    % if form.relationship.errors:
    <dd>${lib.field_errors(form.relationship)}</dd>
    % endif

    ${lib.field(form.remark, rows=8, cols=80)}

    <dd class="standard-form-footer">
        <button>Upload!</button>
    </dd>
</dl>
${h.end_form()}
</section>
