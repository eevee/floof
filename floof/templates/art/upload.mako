<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Upload - Artwork</%def>

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

    <dd><button type="submit">Upload!</button></dd>
</dl>
${h.end_form()}
