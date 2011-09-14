# encoding: utf8
import logging

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config
import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField

from floof import model
from floof.forms import MultiCheckboxField
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end

log = logging.getLogger(__name__)

# XXX this all needs cleaning up, and some ajax, and whatever.
# XXX two forms on one page also raises questions about how best to handle invalid forms
class AddOpenIDForm(wtforms.form.Form):
    new_openid = wtforms.TextField(u'New OpenID', [wtforms.validators.Required()])

class RemoveOpenIDForm(wtforms.form.Form):
    #openids = MultiCheckboxField(u'', coerce=int)
    openids = QuerySelectMultipleField(u'Remove OpenIDs', get_label=lambda row: row.url)

    def validate_openids(form, field):
        if not field.data:
            raise wtforms.ValidationError('You must select at least one OpenID identity URL to delete.')
        if len(field.data) >= len(field._get_object_list()):
            raise wtforms.ValidationError('You must keep at least one OpenID identity URL.')

class AuthenticationForm(wtforms.form.Form):
    cert_auth = wtforms.fields.SelectField(u'Certificate Certificates', choices=[
            (u'disabled', u'Disallow using client certificates for login (default)'),
            (u'allowed', u'Allow using client certificates for login'),
            (u'sensitive_required', u'Allow using client certificates for login; Require for Sensitive Operations'),
            (u'required', u'Require using client certificates for login'),
            ])

    def validate_cert_auth(form, field):
        if field.data in ['required', 'sensitive_required']:
            if not c.user.valid_certificates:
                raise wtforms.ValidationError('You cannot make a selection '
                        'that requires an SSL certificate to log in or to '
                        'change this setting while you have no valid SSL '
                        'certificates registered against your account.')
            if not 'cert' in c.auth.satisfied:
                raise wtforms.ValidationError('To prevent locking yourself '
                        'out, you cannot make a selection that requires an '
                        'SSL certificate to log in or to change this '
                        'setting without first loading this page while the '
                        'certificate is installed in your browser and being '
                        'successfully sent to the site.')

@view_config(
    route_name='controls.openid',
    permission='auth.openid',
    request_method='GET',
    renderer='account/controls/openid.mako')
def openid(context, request):
    user = request.user
    add_openid_form = AddOpenIDForm()
    remove_openid_form = RemoveOpenIDForm()
    remove_openid_form.openids.query = model.session.query(model.IdentityURL).with_parent(user)

    return dict(
        add_openid_form=add_openid_form,
        remove_openid_form=remove_openid_form,
    )

@view_config(
    route_name='controls.openid.add',
    permission='auth.openid',
    request_method='POST',
    renderer='account/controls/openid.mako')
def openid_add(context, request):
    user = request.user
    form = AddOpenIDForm(request.POST) # XXX fetch_post(session, request))

    ret = dict(
        openid_form=form,
    )

    # Add an OpenID identity URL
    if not form.validate():
        return ret

    try:
        return HTTPSeeOther(location=openid_begin(
            identifier=form.new_openid.data,
            return_url=request.route_url('controls.openid.add_finish'),
            request=request,
            sreg=False,
        ))
    except OpenIDError as exc:
        form.new_openid.errors.append(exc.args[0])
        return ret


@view_config(
    route_name='controls.openid.add_finish',
    permission='auth.openid',
    request_method='GET',
    renderer='account/controls/openid.mako')
def openid_add_finish(context, request):
    user = request.user
    # XXX we should put the attempted openid in here
    form = AddOpenIDForm() # XXX fetch_post(session, request))
    remove_form = RemoveOpenIDForm()
    remove_form.openids.query = model.session.query(model.IdentityURL).with_parent(user)

    ret = dict(
        add_openid_form=form,
        remove_openid_form=remove_form,
    )

    # Process a returning OpenID check
    form.validate()  # Ensure new_openid.errors is an appendable list
    try:
        identity_url, identity_webfinger, auth_time, sreg_res = openid_end(request.path_url, request)
    except OpenIDError as exc:
        form.new_openid.errors.append(exc.args[0])
        return ret

    # Allow an OpenID identity to be registered to only one user.
    existing_url = model.session.query(model.IdentityURL) \
        .filter_by(url=identity_url) \
        .first()
    if existing_url:
        if existing_url.user_id == user.id:
            form.new_openid.errors.append(u'You can already authenticate with that OpenID identity.')
        else:
            form.new_openid.errors.append(u'That OpenID identity is already in use by another account.')
        return ret

    openid = model.IdentityURL(url=identity_url)
    user.identity_urls.append(openid)
    request.session.flash(
        u"Added a new identity: {0}".format(identity_url),
        level=u'success', icon=u'user--plus')

    return HTTPSeeOther(location=request.route_url('controls.openid'))

@view_config(
    route_name='controls.openid.remove',
    permission='auth.openid',
    request_method='POST',
    renderer='account/controls/openid.mako')
def openid_remove(context, request):
    user = request.user
    form = RemoveOpenIDForm(request.POST) # XXX fetch_post(session, request))
    form.openids.query = model.session.query(model.IdentityURL).with_parent(user)

    ret = dict(
        remove_openid_form=form,
        add_openid_form=AddOpenIDForm(),
    )

    # Delete one or more OpenID identity URLs
    if not form.validate():
        return ret  # XXX uhh

    for target in form.openids.data:
        request.session.flash(
            u"Removed OpenID identifier: {0}".format(target.url),
            level=u'success')
        model.session.delete(target)
    return HTTPSeeOther(location=request.route_url('controls.openid'))

@view_config(
    route_name='controls.auth',
    permission='auth.method',
    request_method='GET',
    renderer='account/controls/authentication.mako')
def authentication(context, request):
    form = AuthenticationForm(None, request.user) # XXX fetch_post(session, request), c.user)
    return dict(
        form=form,
    )

# XXX this one is full of things to fix
@view_config(
    route_name='controls.auth',
    permission='auth.method',
    request_method='POST',
    renderer='account/controls/authentication.mako')
def authentication_commit(context, request):
    form = AuthenticationForm(request.POST, request.user) # XXX fetch_post(session, request), c.user)
    if request.method == 'POST' and form.validate():
        form.populate_obj(request.user)
        # If the new authentication requirements will knock the
        # user out, give them an extra warning and then redirect
        # them to the login screen.
        # XXX do that, but within the page.  the confirm screen is gone!  and yeah force the logout.  and stuff.
        if 0 and not c.auth.authenticate() and not c.confirm_form.confirm.data:
            pass
        else:
            request.session.flash(u'Authentication options updated.', level=u'success')
            if 0 and not c.auth.authenticate():
                return HTTPSeeOther(request.route_url('account.login'))
            return HTTPSeeOther(location=request.path_url)
    return dict(
        form=form,
    )
