# encoding: utf8
import logging
import re
import unicodedata

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config
import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField

from floof.forms import IDNAField, KeygenField, MultiCheckboxField, TimezoneField
from floof.lib.auth import get_ca, update_crl
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
import floof.model as model
from floof.model import meta

log = logging.getLogger(__name__)

# XXX @logged_in
@view_config(
    route_name='controls.index',
    request_method='GET',
    renderer='account/controls/index.mako')
def index(context, request):
    return {}


class UserInfoForm(wtforms.form.Form):
    display_name = wtforms.fields.TextField(u'Display Name')
    email = IDNAField(u'Email Address', [
            wtforms.validators.Optional(),
            wtforms.validators.Email(message=u'That does not appear to be an email address.'),
            ])
    timezone = TimezoneField(u'Timezone')
    submit = wtforms.SubmitField(u'Update')

    # n.b. model.User.display_name is a mapper, not a column, hence __table__
    _display_name_maxlen = model.User.__table__.c.display_name.type.length

    def validate_display_name(form, field):
        field.data = field.data.strip()

        if len(field.data) > form._display_name_maxlen:
            raise wtforms.ValidationError(
                '{0} characters maximum.'.format(form._display_name_maxlen))

        for char in field.data:
            # Allow printable ASCII
            # XXX Is there a better way than checking ord(char)?
            if 32 <= ord(char) <= 126:
                continue

            # Disallow combining characters regardless of category
            if unicodedata.combining(char):
                raise wtforms.ValidationError('No combining characters.')

            # Allow anything non-ASCII categorized as a letter
            if unicodedata.category(char).startswith('L'):
                continue

            raise wtforms.ValidationError(u'Invalid character: {0}'.format(char))

def reduce_display_name(name):
    """Return a reduced version of a display name for comparison with a
    username.
    """
    # Strip out diacritics
    name = ''.join(char for char in unicodedata.normalize('NFD', name)
                   if not unicodedata.combining(char))

    name = re.sub(r'\s+', '_', name)
    name = name.lower()

    return name

# XXX @logged_in
@view_config(
    route_name='controls.info',
    request_method='GET',
    renderer='account/controls/user_info.mako')
def user_info(context, request):
    form = UserInfoForm(None, request.user)
    return {
        'form': form,
    }

# XXX @logged_in
@view_config(
    route_name='controls.info',
    request_method='POST',
    renderer='account/controls/user_info.mako')
def user_info_commit(context, request):
    user = request.user
    form = UserInfoForm(request.POST, user)

    if not form.validate():
        return {
            'form': form,
        }
        return render_to_response(
            'account/controls/user_info.mako', {'form': form}, request=request)

    form.populate_obj(user)

    if not form.display_name.data:
        user.display_name = None
        user.has_trivial_display_name = False
    else:
        user.has_trivial_display_name = (user.name ==
            reduce_display_name(user.display_name))

    request.session.flash(
        u'Successfully updated user info.',
        # XXX level=u'success'
    )

    return HTTPSeeOther(location=request.path_url)


# XXX @logged_in
@view_config(
    route_name='controls.rels',
    request_method='GET',
    renderer='account/controls/relationships.mako')
def relationships(context, request):
    # XXX: it would be nice to merge this with the view UI, whenever that
    # exists
    # XXX: show timestamps

    q = meta.Session.query(model.UserWatch) \
        .with_parent(request.user) \
        .order_by(model.UserWatch.created_time.desc())
    watches = q.all()

    return {
        'watches': q.all(),
    }

class WatchForm(wtforms.form.Form):
    watch_upload = wtforms.fields.BooleanField(u'')
    watch_by = wtforms.fields.BooleanField(u'')
    watch_for = wtforms.fields.BooleanField(u'')
    watch_of = wtforms.fields.BooleanField(u'')

# XXX does this need a permission
# XXX @logged_in
# XXX not converted oops; needs userpages
def relationships_watch(context, request):
    # XXX clean this crap up
    target_username = request.params.get('target_user', None)
    c.target_user = meta.Session.query(model.User) \
        .filter_by(name=target_username).one()
    if not c.target_user:
        abort(404)

    c.watch = meta.Session.query(model.UserWatch) \
        .filter_by(user_id=c.user.id, other_user_id=c.target_user.id) \
        .first()
    c.watch_form = WatchForm(obj=c.watch)

    return render('/account/controls/relationships_watch.mako')

# XXX does this need a permission
# XXX @logged_in
# XXX not converted oops; needs userpages
def relationships_watch_commit(context, request):
    # XXX clean this crap up
    target_username = request.params.get('target_user', None)
    target_user = meta.Session.query(model.User) \
        .filter_by(name=target_username).one()
    if not target_user:
        abort(404)

    watch_form = WatchForm(request.POST)
    if not watch_form.validate():
        # XXX better redirect whatever
        helpers.flash(u"Yo form is jacked", level=u'error')
        redirect(url.current(target_user=target_username))

    watch = meta.Session.query(model.UserWatch) \
        .filter_by(user_id=c.user.id, other_user_id=target_user.id) \
        .first()
    if not watch:
        watch = model.UserWatch(
            user_id=c.user.id,
            other_user_id=target_user.id,
        )

    watch.watch_upload = watch_form.watch_upload.data
    watch.watch_by = watch_form.watch_by.data
    watch.watch_for = watch_form.watch_for.data
    watch.watch_of = watch_form.watch_of.data

    meta.Session.add(watch)
    meta.Session.commit()

    # XXX where should this redirect?
    helpers.flash(
        u"Saved watch settings for {0}.".format(target_user.display_name),
        level=u'success',
    )
    redirect(url('user', user=target_user))

# XXX does this need a permission
# XXX @logged_in
# XXX not converted oops; needs userpages
def relationships_unwatch_commit(context, request):
    # XXX clean this crap up
    target_username = request.params.get('target_user', None)
    target_user = meta.Session.query(model.User) \
        .filter_by(name=target_username).one()
    if not target_user:
        abort(404)

    if not request.POST.get('confirm', False):
        # XXX better redirect whatever
        helpers.flash(
            u"If you REALLY REALLY want to unwatch {0}, check the box and try again.".format(target_user.display_name),
            level=u'error',
        )
        redirect(url.current(
            action='relationships_watch', target_user=target_username),
            )

    meta.Session.query(model.UserWatch) \
        .filter_by(user_id=c.user.id, other_user_id=target_user.id) \
        .delete()
    meta.Session.commit()

    # XXX where should this redirect?
    helpers.flash(
        u"Unwatched {0}.".format(target_user.display_name),
        level=u'success',
    )
    redirect(url('user', user=target_user))


# XXX this all needs cleaning up, and some ajax, and whatever.
# XXX two forms on one page also raises questions about how best to handle invalid forms
class AddOpenIDForm(wtforms.form.Form):
    new_openid = wtforms.TextField(u'New OpenID', [wtforms.validators.Required()])

class RemoveOpenIDForm(wtforms.form.Form):
    #openids = MultiCheckboxField(u'', coerce=int)
    openids = QuerySelectMultipleField(u'', get_label=lambda row: row.url)

    def validate_openids(form, field):
        if not field.data:
            raise wtforms.ValidationError('You must select at least one OpenID identity URL to delete.')
        if len(field.data) >= len(field._get_object_list()):
            raise wtforms.ValidationError('You must keep at least one OpenID identity URL.')

# XXX @user_must('auth.openid')
@view_config(
    route_name='controls.openid',
    request_method='GET',
    renderer='account/controls/openid.mako')
def openid(context, request):
    user = request.user
    add_openid_form = AddOpenIDForm()
    remove_openid_form = RemoveOpenIDForm()
    remove_openid_form.openids.query = meta.Session.query(model.IdentityURL).with_parent(user)

    return dict(
        add_openid_form=add_openid_form,
        remove_openid_form=remove_openid_form,
    )

# XXX @user_must('auth.openid')
@view_config(
    route_name='controls.openid.add',
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


# XXX @user_must('auth.openid')
@view_config(
    route_name='controls.openid.add_finish',
    request_method='GET',
    renderer='account/controls/openid.mako')
def openid_add_finish(context, request):
    user = request.user
    # XXX we should put the attempted openid in here
    form = AddOpenIDForm() # XXX fetch_post(session, request))
    remove_form = RemoveOpenIDForm()
    remove_form.openids.query = meta.Session.query(model.IdentityURL).with_parent(user)

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
    existing_url = meta.Session.query(model.IdentityURL) \
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
        u"Successfully added OpenID identifier: {0}".format(identity_url),
        # XXX level=u'success'
    )
    return HTTPSeeOther(location=request.route_url('controls.openid'))

# XXX @user_must('auth.openid')
@view_config(
    route_name='controls.openid.remove',
    request_method='POST',
    renderer='account/controls/openid.mako')
def openid_remove(context, request):
    user = request.user
    form = RemoveOpenIDForm(request.POST) # XXX fetch_post(session, request))
    form.openids.query = meta.Session.query(model.IdentityURL).with_parent(user)

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
            # XXX level=u'success'
        )
        meta.Session.delete(target)
    return HTTPSeeOther(location=request.route_url('controls.openid'))


# XXX not used atm
def check_cert(cert, user, check_validity=False):
    if cert is None:
        abort(404, detail='Certificate not found.')
    if cert not in user.certificates:
        abort(403, detail='That does not appear to be your certificate.')
    if check_validity and not c.cert.valid:
        abort(404, detail='That certificate has already expired or been revoked.')

class CertificateForm(wtforms.form.Form):
    # XXX split this in two
    pubkey = KeygenField(u'Public Key')
    days = wtforms.fields.SelectField(u'New Certificate Validity Period',
            coerce=int,
            choices=[(31, '31 days'), (366, '1 year'), (1096, '3 years')]
            )
    name = wtforms.fields.TextField(u'PKCS12 Friendly Name', [
            wtforms.validators.Length(max=64),
            ])
    passphrase = wtforms.fields.PasswordField(u'PKCS12 Passphrase', [
            wtforms.validators.Length(max=64),
            ])
    generate_browser = wtforms.fields.SubmitField(u'Generate In Browser')
    generate_server = wtforms.fields.SubmitField(u'Generate On Server')

    def validate_pubkey(form, field):
        if not field.data and form.generate_browser.data:
            raise wtforms.ValidationError('It looks like your browser '
                    'doesn\'t support this method.  Try &quot;Generate '
                    'Certificate on Server&quot;.')

class RevokeCertificateForm(wtforms.form.Form):
    ok = wtforms.fields.SubmitField(u'Revoke Certificate')
    cancel = wtforms.fields.SubmitField(u'Cancel')

class AuthenticationForm(wtforms.form.Form):
    cert_auth = wtforms.fields.SelectField(u'Certificate Authentication Control', choices=[
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

# XXX @user_must('auth.certificates')
@view_config(
    route_name='controls.certs',
    request_method='GET',
    renderer='account/controls/certificates.mako')
def certificates(context, request, err=None):
    form = CertificateForm()
    if request.method == 'POST' and \
            form.validate() and \
            form.generate_browser.data:
        # Generate a new certificate from UA-supplied key.
        spkac = form.pubkey.data
        cert = model.Certificate(
                request.user,
                *get_ca(),
                spkac=spkac,
                days=form.days.data
                )
        request.user.certificates.append(cert)
        meta.Session.commit()
        helpers.flash(
                u'New certificate generated.  You may need to restart '
                'your browser to begin authenticating with it.',
                level=u'success',
                )
        response.content_type = 'application/x-x509-user-cert'
        return cert.public_data_der
    return dict(
        form=form,
    )

# XXX @user_must('auth.certificates')
@view_config(
    route_name='controls.certs',
    request_method='POST',
    renderer='account/controls/certificates.mako')
def certificates_generate_client(context, request):
    form = CertificateForm(request.POST) # XXX fetch_post(session, request))
    if not form.validate():
        return dict(form=form)

    # Generate a new certificate from UA-supplied key.
    spkac = form.pubkey.data
    cert = model.Certificate(
        request.user,
        *get_ca(request.registry.settings),
        spkac=spkac,
        days=form.days.data
    )
    request.user.certificates.append(cert)
    request.session.flash(
        u'New certificate generated.  You may need to restart '
        'your browser to begin authenticating with it.',
        # XXX level=u'success',
    )
    return Response(
        body=cert.public_data_der,
        headerlist=[('Content-type', 'application/x-x509-user-cert')],
    )

# XXX @user_must('auth.certificates')
@view_config(
    route_name='controls.certs.generate_server',
    request_method='POST',
    renderer='account/controls/certificates.mako')
def certificates_generate_server(context, request):
    form = CertificateForm(request.POST)
    if not form.validate():
        return dict(form=form)

    # Generate a new certificate.
    ca = get_ca(request.registry.settings)
    cert = model.Certificate(
        request.user,
        *ca,
        days=form.days.data
    )
    request.user.certificates.append(cert)
    request.session.flash(
        u'New certificate generated.',
        # XXX level=u'success',
    )
    return Response(
        body=cert.pkcs12(form.passphrase.data, form.name.data, *ca),
        headerlist=[('Content-type', 'application/x-pkcs12')],
    )

# XXX @user_must('auth.certificates')
@view_config(
    route_name='controls.certs.details',
    request_method='GET',
    renderer='account/controls/certificates_details.mako')
def certificates_details(context, request):
    cert = meta.Session.query(model.Certificate).get(request.matchdict['id'])
    # XXX check_cert(c.cert, c.user)
    return dict(cert=cert)

# XXX @user_must('auth.certificates')
@view_config(
    route_name='controls.certs.download',
    request_method='GET')
def certificates_download(context, request):
    cert = meta.Session.query(model.Certificate).get(request.matchdict['id'])
    # XXX check_cert(cert, c.user)
    # TODO: Redirect to the cert overview page.  Somehow.
    return Response(
        body=cert.public_data,
        headerlist=[('Content-type', 'application/x-pem-file')],
    )

# XXX @user_must('auth.certificates')
@view_config(
    route_name='controls.certs.revoke',
    request_method='GET',
    renderer='account/controls/certificates_revoke.mako')
def certificates_revoke(context, request, id=None):
    form = RevokeCertificateForm()
    cert = meta.Session.query(model.Certificate).get(request.matchdict['id'])
    # XXX check_cert(cert, user, check_validity=True)
    will_override_auth = len(request.user.valid_certificates) == 1 and \
            user.cert_auth in ['required', 'sensitive_required']
    return dict(
        form=form,
        cert=cert,
        will_override_auth=will_override_auth,
    )

# XXX @user_must('auth.certificates')
@view_config(
    route_name='controls.certs.revoke',
    request_method='POST')
def certificates_revoke_commit(context, request):
    cert = meta.Session.query(model.Certificate).get(request.matchdict['id'])
    # XXX check_cert(cert, user, check_validity=True)
    cert.revoke()
    update_crl(request.registry.settings)
    # XXX stop naming these by id; use the actual stamp, or date, or something
    request.session.flash(
        u"Certificate ID {0} revoked successfully.".format(cert.id),
        # XXX level=u'success',
    )
    return HTTPSeeOther(location=request.route_url('controls.certs'))

# XXX @user_must('auth.method')
@view_config(
    route_name='controls.auth',
    request_method='GET',
    renderer='account/controls/authentication.mako')
def authentication(context, request):
    form = AuthenticationForm(None, request.user) # XXX fetch_post(session, request), c.user)
    return dict(
        form=form,
    )

# XXX @user_must('auth.method')
# XXX this one is full of things to fix
@view_config(
    route_name='controls.auth',
    request_method='POST',
    renderer='account/controls/authentication.mako')
def authentication_commit(context, request):
    form = AuthenticationForm(request.POST, request.user) # XXX fetch_post(session, request), c.user)
    if request.method =='POST' and form.validate():
        form.populate_obj(request.user)
        # If the new authentication requirements will knock the
        # user out, give them an extra warning and then redirect
        # them to the login screen.
        # XXX do that, but within the page.  the confirm screen is gone!  and yeah force the logout.  and stuff.
        if 0 and not c.auth.authenticate() and not c.confirm_form.confirm.data:
            pass
        else:
            request.session.flash(u'Authentication options updated.', )# XXX level=u'success')
            if 0 and not c.auth.authenticate():
                redirect(url(controller='account', action='login'))
            return HTTPSeeOther(location=request.path_url)
    return dict(
        form=form,
    )
