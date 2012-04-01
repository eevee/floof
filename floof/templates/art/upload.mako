<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />

<%def name="title()">Upload - Artwork</%def>

<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:public/js/uploading.js'))}
</%def>


<section>
    <h1>
        ${lib.icon('image--arrow')}
        Upload
    </h1>

    <%lib:secure_form multipart="${True}" id="upload-form">
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
                <p class="-part-metadata"><br><br><!-- populated by JS --></p>
                <p class="-part-upload"><button type="submit">Upload!</button></p>
            </div>
        </section>
        <section class="column-2x">
            <dl class="standard-form">
                ${lib.field(form.title, size=64, maxlength=133)}
                ${lib.field(form.remark, rows=10, cols=80)}
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
    </%lib:secure_form>
</section>

## TODO i probably want to go in the base template when upload works on every
## page.  if drag&drop is ever intended to work on smaller elements as well,
## though, this and the css rules will need some refinement
<div class="js-dropzone-shield">
    <p>drop here to upload</p>
</div>
