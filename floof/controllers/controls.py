from collections import defaultdict
import logging

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
                        ))
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
        redirect(url('user', user=target_user))

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
                action='relationships_watch', target_user=target_username))

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
