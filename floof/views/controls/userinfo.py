# encoding: utf8
import logging

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config
import wtforms

from floof.forms import DisplayNameField, IDNAField, TimezoneField
from floof.lib.helpers import reduce_display_name

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
