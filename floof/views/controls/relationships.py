# encoding: utf8
import logging

from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPBadRequest, HTTPSeeOther
from pyramid.view import view_config
import wtforms

from floof import model

log = logging.getLogger(__name__)

@view_config(
    route_name='controls.rels',
    permission='__authenticated__',
    request_method='GET',
    renderer='account/controls/relationships.mako')
def relationships(context, request):
    # XXX: it would be nice to merge this with the view UI, whenever that
    # exists
    # XXX: show timestamps

    q = model.session.query(model.UserWatch) \
        .with_parent(request.user) \
        .order_by(model.UserWatch.created_time.desc())

    return {
        'watches': q.all(),
    }

class WatchForm(wtforms.form.Form):
    watch_upload = wtforms.fields.BooleanField(u'')
    watch_by = wtforms.fields.BooleanField(u'')
    watch_for = wtforms.fields.BooleanField(u'')
    watch_of = wtforms.fields.BooleanField(u'')

# XXX does this need a permission
@view_config(
    route_name='controls.rels.watch',
    permission='__authenticated__',
    request_method='GET',
    renderer='account/controls/relationships_watch.mako')
def relationships_watch(context, request):
    target_username = request.params.get('target_user', None)
    target_user = model.session.query(model.User) \
        .filter_by(name=target_username).one()
    if not target_user:
        raise NotFound()

    watch = model.session.query(model.UserWatch) \
        .filter_by(user=request.user, other_user=target_user) \
        .first()
    watch_form = WatchForm(obj=watch)

    return dict(
        target_user=target_user,
        watch=watch,
        watch_form=watch_form,
    )

# XXX does this need a permission
@view_config(
    route_name='controls.rels.watch',
    permission='__authenticated__',
    request_method='POST',
    renderer='account/controls/relationships_watch.mako')
def relationships_watch_commit(context, request):
    # XXX clean this crap up
    target_username = request.params.get('target_user', None)
    target_user = model.session.query(model.User) \
        .filter_by(name=target_username).one()
    if not target_user:
        raise NotFound()

    watch_form = WatchForm(request.POST)
    if not watch_form.validate():
        # XXX better redirect whatever
        request.session.flash(u"Yo form is jacked", level=u'error')
        return HTTPBadRequest()

    watch = model.session.query(model.UserWatch) \
        .filter_by(user=request.user, other_user=target_user) \
        .first()
    if not watch:
        watch = model.UserWatch(
            user=request.user,
            other_user=target_user,
        )

    watch.watch_upload = watch_form.watch_upload.data
    watch.watch_by = watch_form.watch_by.data
    watch.watch_for = watch_form.watch_for.data
    watch.watch_of = watch_form.watch_of.data

    model.session.add(watch)

    # XXX where should this redirect?
    request.session.flash(
        u"Saved watch settings for {0}.".format(target_user.name),
        level=u'success')
    return HTTPSeeOther(request.route_url('users.view', user=target_user))

# XXX does this need a permission
@view_config(
    route_name='controls.rels.unwatch',
    permission='__authenticated__',
    request_method='POST')
def relationships_unwatch_commit(context, request):
    # XXX clean this crap up
    target_username = request.params.get('target_user', None)
    target_user = model.session.query(model.User) \
        .filter_by(name=target_username).one()
    if not target_user:
        raise NotFound()

    if not request.POST.get('confirm', False):
        # XXX better redirect whatever
        request.session.flash(
            u"If you REALLY REALLY want to unwatch {0}, check the box and try again.".format(target_user.name),
            level=u'error')
        return HTTPBadRequest()

    model.session.query(model.UserWatch) \
        .filter_by(user=request.user, other_user=target_user) \
        .delete()

    # XXX where should this redirect?
    request.session.flash(
        u"Unwatched {0}.".format(target_user.name),
        level=u'success')
    return HTTPSeeOther(request.route_url('users.view', user=target_user))
