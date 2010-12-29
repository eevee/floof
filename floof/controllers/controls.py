from collections import defaultdict
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from sqlalchemy.exc import IntegrityError
import wtforms

from floof.lib import helpers
from floof.lib.base import BaseController, render
from floof.lib.decorators import logged_in
import floof.model as model
from floof.model import meta

log = logging.getLogger(__name__)

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
    def relationships(self):
        # XXX: it would be nice to merge this with the view UI, whenever that
        # exists
        # XXX: show timestamps

        c.relationships = defaultdict(list)
        q = meta.Session.query(model.UserRelationship) \
            .filter_by(user_id=c.user.id) \
            .order_by(model.UserRelationship.created_time.desc())
        for rel in q:
            c.relationships[rel.relationship_type].append(rel.other_user)

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
