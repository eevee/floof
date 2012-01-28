<%inherit file="/base.mako" />
<%namespace name="lib" file="/lib.mako" />
<%namespace name="artlib" file="/art/lib.mako" />
<%namespace name="comments_lib" file="/comments/lib.mako" />

<%def name="title()">${artwork.title or 'Untitled'} - Crop</%def>
<%def name="script_dependencies()">
    ${h.javascript_link(request.static_url('floof:public/js/lib/jquery.ui-1.8.7.js'))}
    ${h.javascript_link(request.static_url('floof:public/js/lib/jquery.Jcrop.js'))}
    ${h.javascript_link(request.static_url('floof:public/js/jcrop.js'))}
    ${h.stylesheet_link(request.static_url('floof:public/css/jquery.Jcrop.css'))}
</%def>

<section>
<h1>Crop to ${request.matchdict['action'].capitalize()}:
${artwork.title or 'Untitled'}</h1>

<p>At present, the cropped image must be square.</p>

<%
    max_dim = max(artwork.width, artwork.height)
    scaling = 512.0 / max_dim if max_dim > 512 else 1.0
    width = int(artwork.width * scaling)
    height = int(artwork.height * scaling)
%>\
<section class="crop-control-container">
    <h1>Preview</h1>

    <div class="crop-preview-box clearfix" style="width:${dimension}px; height:${dimension}px;">
        <img id="jcrop-preview" width="${width}" height="${height}"src="${request.route_url('filestore', class_=u'artwork', key=artwork.hash)}" alt="">
    </div>

    <div class="crop-controls">
        ${lib.secure_form(request.path_url)}
        <dl class="standard-form">
            ${lib.field(form.left)}
            ${lib.field(form.top)}
            ${lib.field(form.size)}
            <dd class="standard-form-footer">
                <button>Crop and continue</button>
            </dd>
        </dl>
    </div>

</section>

<section class="crop-selection-container clearfix">
    <h1>Original Image</h1>
    <img id="jcrop-target" width="${width}" height="${height}" src="${request.route_url('filestore', class_=u'artwork', key=artwork.hash)}" alt="">
</section>

<script type="text/javascript">
    var formCoords = {
        'left': $('#${form.left.id}'),
        'top': $('#${form.top.id}'),
        'size': $('#${form.size.id}'),
    };
    $(attachJcropWithPreview($('#jcrop-target'), $('#jcrop-preview'),
                             ${width}, ${height}, ${dimension}, formCoords));
</script>

</section>
