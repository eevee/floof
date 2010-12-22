from collections import defaultdict
import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from floof.lib.base import BaseController, render
from floof.lib.decorators import logged_in
import floof.model as model
from floof.model import meta

log = logging.getLogger(__name__)

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
