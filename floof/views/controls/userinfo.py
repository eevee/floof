# encoding: utf8
import logging
import magic

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config
import wtforms

from floof import model
from floof.forms import DisplayNameField, IDNAField, TimezoneField
from floof.lib.helpers import reduce_display_name
from floof.lib.image import SUPPORTED_MIMETYPES
from floof.lib.image import dump_image_to_buffer, image_hash, thumbnailify

# PIL is an unholy fucking abomination that can't even be imported right
try:
    import Image
except ImportError:
    from PIL import Image

log = logging.getLogger(__name__)

@view_config(
    route_name='controls.index',
    permission='__authenticated__',
    request_method='GET',
    renderer='account/controls/index.mako')
def index(context, request):
    return {}

class UserInfoForm(wtforms.form.Form):
    display_name = DisplayNameField(u'Display name')
    email = IDNAField(u'Email address', [
            wtforms.validators.Optional(),
            wtforms.validators.Email(message=u'That does not appear to be an email address.'),
            ])
    timezone = TimezoneField(u'Timezone')
    submit = wtforms.SubmitField(u'Update')

@view_config(
    route_name='controls.info',
    permission='__authenticated__',
    request_method='GET',
    renderer='account/controls/user_info.mako')
def user_info(context, request):
    form = UserInfoForm(None, request.user)
    return {
        'form': form,
    }

@view_config(
    route_name='controls.info',
    permission='__authenticated__',
    request_method='POST',
    renderer='account/controls/user_info.mako')
def user_info_commit(context, request):
    user = request.user
    form = UserInfoForm(request.POST, user)

    if not form.validate():
        return {'form': form}

    form.populate_obj(user)

    if not form.display_name.data:
        user.display_name = None
        user.has_trivial_display_name = False
    else:
        user.has_trivial_display_name = (user.name ==
            reduce_display_name(user.display_name))

    request.session.flash(
        u'Successfully updated user info.',
        level=u'success')
    return HTTPSeeOther(location=request.path_url)


class UploadAvatarForm(wtforms.form.Form):
    file = wtforms.fields.FileField(u'')
    make_active = wtforms.fields.BooleanField(u'Make Active Avatar', default=False)


@view_config(
    route_name='controls.avatar',
    permission='__authenticated__',
    request_method='GET',
    renderer='account/controls/avatar.mako')
def avatars(context, request):
    return dict(form=UploadAvatarForm())


@view_config(
    route_name='controls.avatar',
    permission='__authenticated__',
    request_method='POST',
    renderer='account/controls/avatar.mako')
def change_avatar(context, request):
    form = UploadAvatarForm(request.POST)
    ret = dict(form=form)

    if not form.validate():
        return ret

    # XXX: The next bunch of lines duplicate some in art.upload

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

    # Open the image, determine its size, and generate a thumbnail'd version
    fileobj.seek(0)
    image = Image.open(fileobj)
    thumbnailed_image = thumbnailify(image, 120, max_aspect_ratio=1,
                                     enlarge=True)
    fileobj = dump_image_to_buffer(thumbnailed_image, mimetype)

    # Hash & store the file.  Reset the file object first!
    fileobj.seek(0)
    hash, file_size = image_hash(fileobj)
    fileobj.seek(0)
    request.storage.put(u'avatar', hash, fileobj)

    width, height = thumbnailed_image.size
    avatar = model.Avatar(
        hash=hash,
        mime_type=mimetype,
        file_size=file_size,
        width=width,
        height=height,
    )
    request.user.avatars.append(avatar)
    model.session.flush()

    if form.make_active.data:
        request.user.avatar = avatar

    request.session.flash(u'Uploaded!', level=u'success', icon=u'image--plus')
    return HTTPSeeOther(location=request.route_url('controls.avatar'))



@view_config(
    route_name='controls.avatar.use',
    permission='avatar.use',
    request_method='POST')
def use_avatar(avatar, request):
    request.user.avatar = avatar
    request.session.flash('Set new avatar.', level='success')
    return HTTPSeeOther(location=request.route_url('controls.avatar'))


@view_config(
    route_name='controls.avatar.use_gravatar',
    permission='__authenticated__',
    request_method='POST')
def use_gravatar(context, request):
    request.user.avatar = None
    request.session.flash('Set new avatar.', level='success')
    return HTTPSeeOther(location=request.route_url('controls.avatar'))


@view_config(
    route_name='controls.avatar.delete',
    permission='avatar.delete',
    request_method='POST')
def delete_avatar(avatar, request):
    if avatar == request.user.avatar:
        # Fall back to Gravatar
        request.user.avatar = None
        model.session.flush()

    request.user.avatars.remove(avatar)
    request.session.flash('Deleted avatar.', level='success', icon='minus')
    return HTTPSeeOther(location=request.route_url('controls.avatar'))
