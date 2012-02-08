<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Upload - Artwork</%def>

<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:public/js/uploading.js'))}
</%def>

<style type="text/css">
body#js-enabled .no-js {
    display: none;
}
body#js-disabled .js {
    display: none;
}
.upload-block {
    text-align: center;
    background: #f9ffff;
}
.upload-block .-part-thumbnail {
    height: 160px;
    width: 160px;
    margin: 0 auto 1em;
    line-height: 160px;
    border: 0.25em solid #eee;
    background: #f4f4f4;
}
.upload-block .-part-thumbnail canvas {
    text-align: center;
    vertical-align: middle;
}
.upload-block button[type='submit'] {
    font-size: 1.33em;
}

.upload-block .-part-file-button {
padding-top: 40px;
}
.upload-block.state-oldmode .-part-file-button,
.upload-block.state-oldmode .-part-thumbnail,
.upload-block.state-init .-part-file-field,
.upload-block.state-init .-part-upload,
.upload-block.state-ready .-part-file-field {
    display: none;
}
</style>



<section>
    <h1>
        ${lib.icon('image--arrow')}
        Upload
    </h1>

    ${lib.secure_form(request.path_url, multipart=True, id="upload-form")}
    <div class="column-container">
        <section class="column">
            <div class="upload-block state-oldmode">
                <p class="-part-file-field">${form.file(multiple=True, accept='image/*')}</p>
                <div class="-part-thumbnail">
                    <p class="-part-file-button">
                        <button type="button">Pick a file</button>
                        <br>
                        <br> or drag and drop
                        <br> from your computer
                    </p>
                </div>
                <p class="-part-upload"><button type="submit">Upload!</button></p>
            </div>
        </section>
        <section class="column-2x">
            ##<h1>Describe it</h1>
            <dl class="standard-form">
                ${lib.field(form.title, size=64, maxlength=133)}
                ${lib.field(form.remark, rows=8, cols=80)}
            </dl>

        </section>
    </div>
        <section>
            <h1>Organize it</h1>
            <dl class="standard-form">
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

                ${lib.field(form.labels)}
                ## TODO thing to add a new label
            </dl>
        </section>
    ${h.end_form()}
</section>

## TODO i probably want to go in the base template when upload works on every
## page.  if drag&drop is ever intended to work on smaller elements as well,
## though, this and the css rules will need some refinement
<div class="js-dropzone-shield">
    <p>drop here to upload</p>
</div>
