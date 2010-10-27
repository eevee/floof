<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Upload - Artwork</%def>

<h1>
    ${lib.icon('image--arrow')}
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
        ${lib.icon('paint-brush')}
        % elif field.data == u'for':
        ${lib.icon('present')}
        % endif
        ${field.label() | n}
    </dd>
    % endfor
    % if c.form.relationship_by_for.errors:
    <dd>${lib.field_errors(c.form.relationship_by_for)}</dd>
    % endif
    <dd>
        ${c.form.relationship_of() | n}
        ${lib.icon('camera')}
        ${c.form.relationship_of.label() | n}
        ${lib.field_errors(c.form.relationship_of)}
    </dd>

    <dd><button type="submit">Upload!</button></dd>
</dl>
${h.end_form()}
