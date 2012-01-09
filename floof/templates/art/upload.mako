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
.upload-block .-upload-thumbnail {
    height: 160px;
    width: 160px;
    margin: 0 auto 1em;
    line-height: 160px;
    border: 0.25em solid #eee;
    background: #f4f4f4;
}
.upload-block .-upload-thumbnail img {
    text-align: center;
    vertical-align: middle;
}
.upload-block button {
    font-size: 1.33em;
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
            <div class="upload-block">
                ${lib.field(form.file, multiple=True, accept='image/*')}
                ##<p><button>Upload!</button></p>
            </div>
        </section>
        <section class="column-2x">
            <dl class="standard-form">
                ${lib.field(form.title, size=64, maxlength=133)}
                ${lib.field(form.remark, rows=8, cols=80)}
            </dl>

            <h1>Organize</h1>
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

                <dd class="standard-form-footer">
                    <button>Upload!</button>
                </dd>
            </dl>
        </section>
    </div>
    ${h.end_form()}
</section>
