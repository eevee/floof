import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort

from floof.lib.base import BaseController, render
from floof.lib.gallery import GalleryView
from floof.lib.helpers import redirect
from floof.model import meta
from floof import model
from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger(__name__)

class TagsController(BaseController):

    def index(self):
        c.tags = meta.Session.query(model.Tag).order_by(model.Tag.name).all()
        return render('/tags/index.mako')

    def view(self, name):
        try:
            tag = meta.Session.query(model.Tag).filter_by(name=name).one()
        except NoResultFound:
            abort(404)

        c.tag = tag
        return render('/tags/view.mako')

    def artwork(self, name):
        """Show a gallery of artwork for this tag."""
        c.tag = name
        c.gallery_view = GalleryView()
        c.gallery_view.filter_by_tag(name)

        return render('/tags/artwork.mako')
