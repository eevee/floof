# encoding: utf8
from __future__ import division
from cStringIO import StringIO
import hashlib
import logging

import magic
from pyramid.httpexceptions import HTTPBadRequest, HTTPSeeOther
from pyramid.view import view_config, view_defaults
import wtforms.form, wtforms.fields, wtforms.validators

from floof import model
from floof.forms import MultiCheckboxField, MultiTagField, QueryMultiCheckboxField
from floof.lib.gallery import GallerySieve
from floof.views._workflow import FormWorkflow

# PIL is an unholy fucking abomination that can't even be imported right
try:
    import Image
except ImportError:
    from PIL import Image

log = logging.getLogger(__name__)

HASH_BUFFER_SIZE = 524288  # .5 MiB
MAX_ASPECT_RATIO = 2


# XXX import from somewhere
class CommentForm(wtforms.form.Form):
    message = wtforms.fields.TextAreaField(label=u'')


def get_number_of_colors(image):
    """Does what it says on the tin.

    This attempts to return the number of POSSIBLE colors in the image, not the
    number of colors actually used.  In the case of a paletted image, PIL is
    often limited to only returning the actual number of colors.  But that's
    usually what we mean for palettes, so eh.

    But full-color images will always return 16777216.  Alpha doesn't count, so
    RGBA is still 24-bit color.
    """
    # See http://www.pythonware.com/library/pil/handbook/concepts.htm for list
    # of all possible PIL modes
    mode = image.mode
    if mode == '1':
        return 2
    elif mode == 'L':
        return 256
    elif mode == 'P':
        # This is sort of (a) questionable and (b) undocumented, BUT:
        # palette.getdata() returns a tuple of mode and raw bytes.  The raw
        # bytes are rgb encoded as three bytes each, so its length is three
        # times the number of palette entries.
        palmode, paldata = image.palette.getdata()
        return len(paldata) / 3
    elif mode in ('RGB', 'RGBA', 'CMYK', 'YCbCr', 'I', 'F',
        'LA', 'RGBX', 'RGBa'):
        return 2 ** 24
    else:
        raise ValueError("Unknown palette mode, argh!")


@view_defaults(
    route_name='art.upload',
    permission='art.upload',
    renderer='art/upload.mako')
class UploadPage(FormWorkflow):
    """Uploads something.  Sort of important, you know."""

    class form_class(wtforms.form.Form):
        # XXX need some kinda field lengths or something on these
        file = wtforms.fields.FileField(u'')
        title = wtforms.fields.TextField(u'Title')
        relationship = MultiCheckboxField(u'',
            choices=[
                (u'by',  u"by me: I'm the artist; I created this!"),
                #(u'for', u"for me: I commissioned this, or it was a gift specifically for me"),
                (u'of',  u"of me: I'm depicted in this artwork"),
            ],
        )
        tags = MultiTagField(u'Tags')

        albums = None  # I am populated dynamically based on user

        remark = wtforms.fields.TextAreaField(u'Remark')

    def make_form(self):
        # Tack album fields onto the form
        class DerivedForm(self.form_class):
            albums = QueryMultiCheckboxField(u'Albums',
                query_factory=lambda: model.session.query(model.Album).with_parent(self.request.user),
                get_label=lambda album: album.name,
            )
        return DerivedForm(self.request.POST)


    @view_config(
        request_method='POST')
    def handle_post(self):
        request = self.request
        form = self.form

        if not form.validate():
            return self.respond_form_error()

        # Grab the file
        storage = request.storage
        uploaded_file = request.POST.get('file')

        # TODO can this be part of the form validation?
        try:
            fileobj = uploaded_file.file
        except AttributeError:
            self.request.session.flash(
                u'Please select a file to upload!',
                level=u'error')
            return self.respond_general_error()

        # Figure out mimetype (and if we even support it)
        mimetype = magic.Magic(mime=True).from_buffer(fileobj.read(1024)) \
            .decode('ascii')
        if mimetype not in (u'image/png', u'image/gif', u'image/jpeg'):
            # XXX this seems suboptimal, but...
            form.file.errors.append("Only PNG, GIF, and JPEG are supported at the moment.")
            return self.respond_form_invalid()

        # Hash the thing
        hasher = hashlib.sha256()
        file_size = 0
        fileobj.seek(0)
        while True:
            buffer = fileobj.read(HASH_BUFFER_SIZE)
            if not buffer:
                break

            file_size += len(buffer)
            hasher.update(buffer)
        hash = hasher.hexdigest().decode('ascii')

        # Assert that the thing is unique
        existing_artwork = model.session.query(model.Artwork) \
            .filter_by(hash = hash) \
            .limit(1) \
            .all()
        if existing_artwork:
            self.request.session.flash(
                u'This artwork has already been uploaded.',
                level=u'warning',
                icon=u'image-import')
            return self.respond_redirect(
                request.route_url('art.view', artwork=existing_artwork[0]))

        ### By now, all error-checking should be done.

        # OK, store the file.  Reset the file object first!
        fileobj.seek(0)
        storage.put(u'artwork', hash, fileobj)

        # Open the image, determine its size, and generate a thumbnail
        fileobj.seek(0)
        image = Image.open(fileobj)
        width, height = image.size

        # Thumbnailin'
        # NOTE: this logic is replicated in the upload JS; please keep in sync
        thumbnail_size = int(request.registry.settings['thumbnail_size'])
        # To avoid super-skinny thumbnails, don't let the aspect ratio go
        # beyond 2
        height = min(height, width * MAX_ASPECT_RATIO)
        width = min(width, height * MAX_ASPECT_RATIO)
        # crop() takes left, top, right, bottom
        cropped_image = image.crop((0, 0, width, height))
        # And resize...  if necessary
        if width > thumbnail_size or height > thumbnail_size:
            if width > height:
                new_size = (thumbnail_size, height * thumbnail_size // width)
            else:
                new_size = (width * thumbnail_size // height, thumbnail_size)

            thumbnail_image = cropped_image.resize(
                new_size, Image.ANTIALIAS)

        else:
            thumbnail_image = cropped_image

        # Dump the thumbnail in a buffer and save it, too
        buf = StringIO()
        if mimetype == u'image/png':
            thumbnail_format = 'PNG'
        elif mimetype == u'image/gif':
            thumbnail_format = 'GIF'
        elif mimetype == u'image/jpeg':
            thumbnail_format = 'JPEG'
        thumbnail_image.save(buf, thumbnail_format)
        buf.seek(0)
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

        # Associate the uploader as an artist
        artwork.user_artwork.append(
            model.UserArtwork(
                user_id = request.user.id,
            )
        )

        # Attach tags and albums
        for tag in form.tags.data:
            artwork.tags.append(tag)

        for album in form.albums.data:
            artwork.albums.append(album)


        model.session.add_all([artwork, discussion, resource])
        model.session.flush()  # for primary keys

        self.request.session.flash(
            u'Uploaded!',
            level=u'success',
            icon=u'image--plus')

        # Success
        return self.respond_redirect(
            request.route_url('art.view', artwork=artwork))

    @view_config(
        request_method='GET',
        xhr=False)
    def handle_get(self):
        return self.show_form()




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
    try:
        rating = int(request.POST['rating'])
    except (KeyError, ValueError):
        return HTTPBadRequest()

    if rating not in (1, 0, -1):
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
            rating_sum=artwork.rating_score,
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
