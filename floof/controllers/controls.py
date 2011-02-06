from collections import defaultdict
import logging

import OpenSSL.crypto as ssl
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from sqlalchemy.exc import IntegrityError
import wtforms

from floof.forms import MultiCheckboxField
from floof.lib import helpers
from floof.lib.base import BaseController, render
from floof.lib.decorators import logged_in
from floof.lib.openid_ import OpenIDError, openid_begin, openid_end
import floof.model as model
from floof.model import meta

log = logging.getLogger(__name__)

# XXX: Should add and delete be seperate forms?
class OpenIDForm(wtforms.form.Form):
    new_openid = wtforms.TextField(u'New OpenID')
    add_openid = wtforms.SubmitField(u'Add OpenID')
    openids = MultiCheckboxField(u'OpenIDs', coerce=int)
    del_openids = wtforms.SubmitField(u'Delete Selected Identities')

    def validate_new_openid(form, field):
        if not form.add_openid.data:
            return
        if not field.data:
            raise wtforms.ValidationError('You must supply a new OpenID URL.')

    def validate_openids(form, field):
        if not form.del_openids.data:
            return
        if len(field.choices) < 2:
            raise wtforms.ValidationError('You must keep at least one OpenID identity URL.')
        if not field.data:
            raise wtforms.ValidationError('You must select at least one OpenID identity URL to delete.')
        if len(field.data) >= len(field.choices):
            raise wtforms.ValidationError('You must keep at least one OpenID identity URL.')

class WatchForm(wtforms.form.Form):
    watch_upload = wtforms.fields.BooleanField(u'')
    watch_by = wtforms.fields.BooleanField(u'')
    watch_for = wtforms.fields.BooleanField(u'')
    watch_of = wtforms.fields.BooleanField(u'')

class CertificateForm(wtforms.form.Form):
    days = wtforms.fields.SelectField(u'New Certificate Validity Period',
            coerce=int,
            choices=[(31, '31 days'), (366, '1 year'), (1096, '3 years')]
            )
    generate = wtforms.fields.SubmitField(u'Generate New Certificate')

class RevokeCertificateForm(wtforms.form.Form):
    ok = wtforms.fields.SubmitField(u'Revoke Certificate')
    cancel = wtforms.fields.SubmitField(u'Cancel')

class DownloadCertificateForm(wtforms.form.Form):
    passphrase = wtforms.fields.PasswordField(u'Passphrase', [
            wtforms.validators.Optional(),
            wtforms.validators.Length(max=64),
            ])
    download = wtforms.fields.SubmitField(u'Download Certificate')

class AuthenticationForm(wtforms.form.Form):
    auth_method = wtforms.fields.SelectField(u'Authentication Method', choices=[
            (u'openid_only', u'OpenID Only (default)'),
            (u'cert_or_openid', u'Certificate OR OpenID (1)'),
            (u'cert_and_openid', u'Certificate AND OpenID (2)'),
            (u'cert_only', u'Certificate Only (1) (2)'),
            ])

    def validate_auth_method(form, field):
        if field.data in ['cert_only', 'cert_and_openid']:
            if not c.user.valid_certificates:
                raise wtforms.ValidationError('You cannot make a selection '
                        'that requires an SSL certificate to log in '
                        'while you have no valid SSL certificates '
                        'registered against your account.')
            if not c.auth.mechanisms['cert']:
                raise wtforms.ValidationError('To prevent locking yourself '
                        'out, you cannot make a selection that requires an '
                        'SSL certificate to log in without first loading '
                        'this page while the certificate is installed in '
                        'your browser and being successfully sent to the '
                        'site.')

class AuthenticationConfirmationForm(wtforms.form.Form):
    confirm = wtforms.fields.SubmitField(u'Confirm Authentication Method Change')
    cancel = wtforms.fields.SubmitField(u'Cancel')


class ControlsController(BaseController):

    @logged_in
    def index(self):
        c.current_action = 'index'
        return render('/account/controls/index.mako')

    @logged_in
    def openid(self):
        c.current_action = 'openid'
        c.openid_form = OpenIDForm(request.POST)
        c.openid_form.openids.choices = [(oid.id, oid.url) for oid in c.user.identity_urls]

        # Process a returning OpenID check
        # XXX: Is this an appropriate way to catch an OpenID response?
        if 'openid.assoc_handle' in request.params:
            c.openid_form.validate()  # Ensure new_openid.errors is an appendable list
            try:
                identity_url, identity_webfinger, sreg_res = openid_end(url.current(host=request.headers['host']))
            except OpenIDError as exc:
                c.openid_form.new_openid.errors.append(exc.args[0])
                return render('/account/controls/openid.mako')

            existing_urls = [id.url for id in c.user.identity_urls]
            if identity_url in existing_urls:
                c.openid_form.new_openid.errors.append(u'You can already authenticate with that OpenID identity.')
                return render('/account/controls/openid.mako')

            # XXX: Allow an OpenID identity to be registered to only one user.
            url_count = meta.Session.query(model.IdentityURL) \
                    .filter_by(url=identity_url) \
                    .count()
            if url_count > 0:
                c.openid_form.new_openid.errors.append(u'That OpenID identity is already in use by another account.')
                return render('/account/controls/openid.mako')

            openid = model.IdentityURL(url=identity_url)
            c.user.identity_urls.append(openid)
            meta.Session.commit()
            helpers.flash(
                    u'Successfully added OpenID identifier "{0}"'
                    .format(identity_url),
                    level=u'success'
                    )
            c.openid_form.openids.choices = [(oid.id, oid.url) for oid in c.user.identity_urls]
            return render('/account/controls/openid.mako')

        # Add an OpenID identity URL
        if (request.method == 'POST' and
                c.openid_form.add_openid.data and
                c.openid_form.validate()):
            try:
                redirect(openid_begin(
                        identifier=c.openid_form.new_openid.data,
                        return_url=url.current(host=request.headers['host']),
                        sreg=False,
                        ), code=303)
            except OpenIDError as exc:
                c.openid_form.new_openid.errors.append(exc.args[0])
                return render('/account/controls/openid.mako')

        # Delete one or more OpenID identity URLs
        if (request.method == 'POST' and
                c.openid_form.del_openids.data and
                c.openid_form.validate()):
            del_targets = filter(lambda oid: oid.id in c.openid_form.openids.data, c.user.identity_urls)
            target_urls = [oid.url for oid in del_targets]
            for target in del_targets:
                meta.Session.delete(target)
            helpers.flash(
                    u'Successfully deleted the OpenID identifier{0}: "{1}"'
                    .format(('s' if len(target_urls) == 1 else ''), '", "'.join(target_urls)),
                    level=u'success'
                    )
            meta.Session.commit()

        # Non-OpenID response GET request, successful delete or invalid form -- just show the page
        c.openid_form.openids.choices = [(oid.id, oid.url) for oid in c.user.identity_urls]
        return render('/account/controls/openid.mako')


    @logged_in
    def relationships(self):
        # XXX: it would be nice to merge this with the view UI, whenever that
        # exists
        # XXX: show timestamps

        q = meta.Session.query(model.UserWatch) \
            .filter_by(user_id=c.user.id) \
            .order_by(model.UserWatch.created_time.desc())
        c.watches = q.all()

        c.current_action = 'relationships'
        return render('/account/controls/relationships.mako')

    # XXX does this need a permission
    @logged_in
    def relationships_watch(self):
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

        c.current_action = None
        return render('/account/controls/relationships_watch.mako')

    # XXX does this need a permission
    @logged_in
    def relationships_watch_commit(self):
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
        redirect(url('user', user=target_user), code=303)

    # XXX does this need a permission
    @logged_in
    def relationships_unwatch_commit(self):
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
                code=303,
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
        redirect(url('user', user=target_user), code=303)

    @logged_in
    def certificates(self):
        c.current_action = 'certificates'
        c.form = CertificateForm(request.POST)
        if request.method == 'POST' and \
                c.form.validate() and \
                c.form.generate.data:
            # Generate a new certificate.
            cert = model.Certificate(c.user, days=c.form.days.data)
            c.user.certificates.append(cert)
            meta.Session.commit()
            helpers.flash(
                    u'New certificate generated.',
                    level=u'success',
                    )
            return redirect(url.current(), code=303)
        return render('/account/controls/certificates.mako')

    @logged_in
    def certificates_details(self, id=None):
        c.current_action = None
        c.cert = model.Certificate.get(meta.Session, id=id)
        if c.cert is None:
            abort(404)
        if c.cert not in c.user.certificates:
            abort(403)
        return render('/account/controls/certificates_details.mako')

    @logged_in
    def certificates_download_prep(self, id=None):
        c.current_action = None
        c.form = DownloadCertificateForm(request.POST)
        c.cert = model.Certificate.get(meta.Session, id=id)
        if c.cert is None:
            abort(404, detail='Certificate not found.')
        if c.cert not in c.user.certificates:
            abort(403, detail='That does not appear to be your certificate.')
        return render('/account/controls/certificates_download.mako')

    @logged_in
    def certificates_download(self, id=None):
        c.form = DownloadCertificateForm(request.POST)
        cert = model.Certificate.get(meta.Session, id=id)
        if cert is None:
            abort(404, detail='Certificate not found.')
        if cert not in c.user.certificates:
            abort(403, detail='That does not appear to be your certificate.')
        if not c.form.validate():
            redirect(url(controller='controls', action='certificates_download_prep'), code=303)
        response.content_type = "application/x-pkcs12"
        if c.form.passphrase.data:
            pkcs12 = ssl.load_pkcs12(cert.pkcs12_data)
            return pkcs12.export(c.form.passphrase.data)
        return cert.pkcs12_data

    @logged_in
    def certificates_revoke(self, id=None):
        c.current_action = 'certificates'
        c.form = RevokeCertificateForm(request.POST)
        c.cert = model.Certificate.get(meta.Session, id=id)
        if c.cert is None:
            abort(404, detail='Certificate not found.')
        if c.cert not in c.user.certificates:
            abort(403, detail='That does not appear to be your certificate.')
        if not c.cert.valid:
            abort(404, detail='That certificate has already expired or been revoked.')
        c.will_override_auth = len(c.user.valid_certificates) == 1 and \
                c.user.auth_method in ['cert_only', 'cert_and_openid']
        if request.method == 'POST' and c.form.validate():
            if c.form.ok.data:
                c.cert.revoke()
                meta.Session.commit()
                helpers.flash(
                        u'Certificate ID {0} revoked successfully.' \
                                .format(c.cert.id),
                        level=u'success',
                        )
            redirect(url(controller='controls', action='certificates'), code=303)
        return render('/account/controls/certificates_revoke.mako')

    @logged_in
    def authentication(self):
        c.current_action = 'authentication'
        c.form = AuthenticationForm(request.POST, c.user)
        c.confirm_form = AuthenticationConfirmationForm(request.POST)
        c.need_confirmation = False
        c.confirm_form.validate()
        if c.confirm_form.cancel.data:
            redirect(url.current(), code=303)
        if request.POST and c.form.validate():
            c.form.populate_obj(c.user)
            # If the new authentication requirements will knock the
            # user out, give them an extra warning and then redirect
            # them to the login screen
            if not c.auth.authenticate() and not c.confirm_form.confirm.data:
                c.need_confirmation = True
            else:
                meta.Session.commit()
                helpers.flash(u'Authentication options updated.', level=u'success')
                if not c.auth.authenticate():
                    redirect(url(controller='account', action='login'), code=303)
                redirect(url.current(), code=303)
        return render('/account/controls/authentication.mako')
