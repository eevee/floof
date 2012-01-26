# encoding: utf8
from __future__ import division
import logging

import magic
from pyramid.httpexceptions import HTTPBadRequest, HTTPSeeOther
from pyramid.view import view_config
import wtforms.form, wtforms.fields, wtforms.validators

from floof import model
from floof.forms import FloofForm, MultiCheckboxField, MultiTagField
from floof.forms import QueryMultiCheckboxField, RequiredValidator
from floof.lib.image import SUPPORTED_MIMETYPES
from floof.lib.image import dump_image_to_buffer, get_number_of_colors
from floof.lib.image import image_hash, scaled_dimensions, thumbnailify
from floof.lib.gallery import GallerySieve

# XXX import from somewhere
class CommentForm(wtforms.form.Form):
    message = wtforms.fields.TextAreaField(label=u'')

# PIL is an unholy fucking abomination that can't even be imported right
try:
    import Image
except ImportError:
    from PIL import Image

log = logging.getLogger(__name__)

HASH_BUFFER_SIZE = 524288  # .5 MiB
MAX_ASPECT_RATIO = 2


class UploadArtworkForm(wtforms.form.Form):
    # XXX need some kinda field lengths or something on these
    file = wtforms.fields.FileField(u'')
    title = wtforms.fields.TextField(u'Title')
    relationship = MultiCheckboxField(u'',
        choices=[
            (u'by',  u"by me: I'm the artist; I created this!"),
            (u'for', u"for me: I commissioned this, or it was a gift specifically for me"),
            (u'of',  u"of me: I'm depicted in this artwork"),
        ],
    )
    tags = MultiTagField(u'Tags')

    labels = None  # I am populated dynamically based on user

    remark = wtforms.fields.TextAreaField(u'Remark')


@view_config(
    route_name='art.upload',
    permission='art.upload',
    # XXX request_method='GET',
    renderer='art/upload.mako')
def upload(context, request):
    """Uploads something.  Sort of important, you know."""
    # Tack label fields onto the form
    class DerivedForm(UploadArtworkForm):
        labels = QueryMultiCheckboxField(u'Labels',
            query_factory=lambda: model.session.query(model.Label).with_parent(request.user),
            get_label=lambda label: label.name,
        )

    form = DerivedForm(request.POST)
    ret = dict(form=form)

    # XXX this overloading is dummmmmb
    if request.method != 'POST' or not form.validate():
        # Initial request, or bogus form submission
        return ret

    # Grab the file
    storage = request.storage
    uploaded_file = request.POST.get('file')

    try:
        fileobj = uploaded_file.file
    except AttributeError:
        form.file.errors.append("Please select a file to upload!")
        return ret

    # Figure out mimetype (and if we even support it)
    mimetype = magic.Magic(mime=True).from_buffer(fileobj.read(1024)) \
        .decode('ascii')
    if mimetype not in SUPPORTED_MIMETYPES:
        form.file.errors.append("Only PNG, GIF, and JPEG are supported at the moment.")
        return ret

    # Hash the thing
    fileobj.seek(0)
    hash, file_size = image_hash(fileobj)

    # Assert that the thing is unique
    existing_artwork = model.session.query(model.Artwork) \
        .filter_by(hash = hash) \
        .all()
    if existing_artwork:
        request.session.flash(
            u'This artwork has already been uploaded.',
            level=u'warning', icon=u'image-import')
        return HTTPSeeOther(location=request.route_url('art.view', artwork=existing_artwork[0]))

    ### By now, all error-checking should be done.

    # OK, store the file.  Reset the file object first!
    fileobj.seek(0)
    storage.put(u'artwork', hash, fileobj)

    # Open the image, determine its size, and generate a thumbnail
    fileobj.seek(0)
    image = Image.open(fileobj)
    width, height = image.size

    # Thumbnailin'
    thumbnail_size = int(request.registry.settings['thumbnail_size'])
    # To avoid super-skinny thumbnails, don't let the aspect ratio go
    # beyond 2
    thumbnail_image = thumbnailify(image, thumbnail_size, max_aspect_ratio=2)

    # Dump the thumbnail in a buffer and save it, too
    buf = dump_image_to_buffer(thumbnail_image, mimetype)
    storage.put(u'thumbnail', hash, buf)

    # Deal with user-supplied metadata
    # nb: it's perfectly valid to have no title or remark
    title = form.title.data.strip()
    remark = form.remark.data.strip()

    # Stuff it all in the db
    resource = model.Resource(type=u'artwork')
    discussion = model.Discussion(resource=resource)
    general_data = dict(
        title = title,
        hash = hash,
        uploader = request.user,
        original_filename = uploaded_file.filename,
        mime_type = mimetype,
        file_size = file_size,
        resource = resource,
        remark = remark,
    )
    artwork = model.MediaImage(
        height = height,
        width = width,
        number_of_colors = get_number_of_colors(image),
        **general_data
    )

    # Associate the uploader as artist or recipient
    # Also as a participant if appropriate
    for relationship in form.relationship.data:
        artwork.user_artwork.append(
            model.UserArtwork(
                user_id = request.user.id,
                relationship_type = relationship,
            )
        )

    # Attach tags and labels
    for tag in form.tags.data:
        artwork.tags.append(tag)

    for label in form.labels.data:
        artwork.labels.append(label)


    model.session.add_all([artwork, discussion, resource])
    model.session.flush()  # for primary keys

    request.session.flash(u'Uploaded!', level=u'success', icon=u'image--plus')
    return HTTPSeeOther(location=request.route_url('art.view', artwork=artwork))


@view_config(
    route_name='art.browse',
    request_method='GET',
    renderer='art/gallery.mako')
def browse(context, request):
    """Main gallery; provides browsing through absolutely everything we've
    got.
    """
    gallery_sieve = GallerySieve(user=request.user, formdata=request.GET)
    return dict(gallery_sieve=gallery_sieve)

@view_config(
    route_name='art.view',
    request_method='GET',
    renderer='art/view.mako')
def view(artwork, request):
    # If the user is not anonymous, get the previous rating if it exists
    current_rating = None
    if request.user:
        rating_obj = model.session.query(model.ArtworkRating) \
            .with_parent(artwork) \
            .with_parent(request.user) \
            .first()

        if rating_obj:
            current_rating = rating_obj.rating

    return dict(
        artwork=artwork,
        current_rating=current_rating,
        comment_form=CommentForm(),
        add_tag_form=AddTagForm(),
        remove_tag_form=RemoveTagForm(),
    )


@view_config(
    route_name='art.rate',
    permission='art.rate',
    request_method='POST')
@view_config(
    route_name='art.rate',
    request_method='POST',
    xhr=True,
    renderer='json')
def rate(artwork, request):
    """Post a rating for a piece of art"""
    radius = int(request.registry.settings['rating_radius'])
    try:
        rating = int(request.POST['rating']) / radius
    except (KeyError, ValueError):
        return HTTPBadRequest()

    # Get the previous rating, if there was one
    rating_obj = model.session.query(model.ArtworkRating) \
        .filter_by(artwork=artwork, user=request.user) \
        .first()

    # Update the rating or create it and add it to the db.
    # n.b.: The model is responsible both for ensuring that the rating is
    # within [-1, 1], and updating rating stats on the artwork
    if rating_obj:
        rating_obj.rating = rating
    else:
        rating_obj = model.ArtworkRating(
            artwork=artwork,
            user=request.user,
            rating=rating,
        )
        model.session.add(rating_obj)

    # If the request has the asynchronous parameter, we return the number/sum
    # of ratings to update the widget
    if request.is_xhr:
        return dict(
            ratings=artwork.rating_count,
            rating_sum=artwork.rating_score * radius,
        )

    # Otherwise, we're probably dealing with a no-js request and just re-render
    # the art page
    return HTTPSeeOther(location=request.route_url('art.view', artwork=artwork))


class AddTagForm(wtforms.form.Form):
    tags = MultiTagField(
        u"Add a tag",
        [wtforms.validators.Required()],
        id='add_tags',
    )

    def __init__(self, *args, **kwargs):
        self._artwork = kwargs.get('artwork', None)
        super(AddTagForm, self).__init__(*args, **kwargs)

    def validate_tags(form, field):
        if field.data is not None:
            for tag in field.data:
                if tag in form._artwork.tags:
                    raise ValueError("Already tagged with \"{0}\"".format(tag))

@view_config(
    route_name='art.add_tags',
    permission='tags.add',
    request_method='POST')
def add_tags(artwork, request):
    form = AddTagForm(request.POST, artwork=artwork)
    if not form.validate():
        # FIXME when the final UI is figured out
        return HTTPBadRequest()

    for tag in form.tags.data:
        artwork.tags.append(tag)

    if len(form.tags.data) == 1:
        request.session.flash(u"Tag \"{0}\" has been added".format(tag))
    else:
        request.session.flash(u"Your tags have been added")

    return HTTPSeeOther(location=request.route_url('art.view', artwork=artwork))

class RemoveTagForm(wtforms.form.Form):
    tags = MultiTagField(
        u"Remove a tag",
        [wtforms.validators.Required()],
        id='remove_tags',
    )

    def __init__(self, *args, **kwargs):
        self._artwork = kwargs.get('artwork', None)
        super(RemoveTagForm, self).__init__(*args, **kwargs)

    def validate_tags(form, field):
        if field.data is not None:
            for tag in field.data:
                if tag not in form._artwork.tags:
                    raise ValueError(u"Not tagged with \"{0}\"".format(tag))

@view_config(
    route_name='art.remove_tags',
    permission='tags.remove',
    request_method='POST')
def remove_tags(artwork, request):
    form = RemoveTagForm(request.POST, artwork=artwork)
    if not form.validate():
        # FIXME when the final UI is figured out
        return HTTPBadRequest()

    for tag in form.tags.data:
        artwork.tags.remove(tag)

    if len(form.tags.data) == 1:
        request.session.flash(u"Tag \"{0}\" has been removed".format(tag))
    else:
        request.session.flash(u"Tags have been removed")

    return HTTPSeeOther(location=request.route_url('art.view', artwork=artwork))


CROPPED_SIZE = 250
ORIG_MAX_SIZE = 512


class CropImageForm(FloofForm):
    left = wtforms.fields.IntegerField(u'Left', [
        RequiredValidator(),
        wtforms.validators.NumberRange(min=0, max=None),
        ])
    top = wtforms.fields.IntegerField(u'Top', [
        RequiredValidator(),
        wtforms.validators.NumberRange(min=0, max=None),
        ])
    size = wtforms.fields.IntegerField(u'Size', [
        RequiredValidator(),
        wtforms.validators.NumberRange(min=1, max=None),
        ])

    def _check_position(form, field):
        artwork = form.request.context
        width, height = scaled_dimensions(artwork, max_size=ORIG_MAX_SIZE)
        max_value = width if field.short_name == 'left' else height
        extremity = 'right' if field.short_name == 'left' else 'bottom'

        if field.data >= max_value:
            raise wtforms.validators.ValidationError(
                    'Number must be less than the {0} edge of the image ({1}px).'
                    .format(extremity, max_value))

    def validate_left(form, field):
        form._check_position(field)

    def validate_top(form, field):
        form._check_position(field)

    def validate_size(form, field):
        artwork = form.request.context
        width, height = scaled_dimensions(artwork, max_size=ORIG_MAX_SIZE)
        max_size = min(width - form.left.data, height - form.top.data)
        if max_size > 0 and field.data > max_size:
            raise wtforms.validators.ValidationError(
                    'The cropped image must not exceed the edges of the '
                    'original (for the current Left & Top, max size is '
                    '({0}px).'.format(max_size))


@view_config(
    route_name='art.crop',
    permission='art.derive',
    request_method='GET',
    renderer='art/crop.mako')
def crop(artwork, request):
    width, height = scaled_dimensions(artwork, max_size=ORIG_MAX_SIZE)
    return dict(
        artwork=artwork,
        dimension=CROPPED_SIZE,
        form=CropImageForm(request, prefix='jcrop-'),
        width=width,
        height=height,
    )


@view_config(
    route_name='art.crop',
    permission='art.derive',
    request_method='POST',
    renderer='art/crop.mako')
def crop_do(artwork, request):
    form = CropImageForm(request, request.POST, prefix='jcrop-')

    width, height = scaled_dimensions(artwork, max_size=ORIG_MAX_SIZE)

    if not form.validate():
        return dict(
            artwork=artwork,
            dimension=CROPPED_SIZE,
            form=form,
            width=width,
            height=height,
        )

    from pyramid.response import Response
    from floof.lib.image import unscaled_coords
    from urllib2 import urlopen
    from cStringIO import StringIO
    left, top, size = form.left.data, form.top.data, form.size.data
    # (left, top, right, bottom)
    coords = (left, top, left + size, top + size)
    coords = unscaled_coords(artwork, ORIG_MAX_SIZE, coords)
    storage = request.registry.settings['filestore']
    url = storage.url(u'artwork', artwork.hash)
    buf = urlopen(url, timeout=10)
    buf = StringIO(buf.read())
    image = Image.open(buf)
    cropped_image = thumbnailify(
            image, CROPPED_SIZE, crop_coords=coords, max_aspect_ratio=1,
            enlarge=True)
    return Response(
        body=dump_image_to_buffer(cropped_image, 'image/png').read(),
        headerlist=[('Content-type', 'image/png')],
    )
