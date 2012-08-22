import logging

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.decorator import reify
from pyramid.security import authenticated_userid
from sqlalchemy import engine_from_config
from sqlalchemy.orm.exc import NoResultFound
from zope.sqlalchemy import ZopeTransactionExtension

from floof import model
from floof.api.auth import FloofAPIAuthnPolicy
from floof.api.auth import token_from_request
from floof.app import FloofRequest
from floof.lib.authz import add_user_authz_methods
from floof.model import filestore
from floof.resource import FloofRoot

import floof.api.views
import floof.routing

log = logging.getLogger(__name__)


class FloofAPIRequest(FloofRequest):
    auth = None

    @reify
    def token(self):
        return token_from_request(self)

    @reify
    def user(self):
        uid = authenticated_userid(self)

        user = model.AnonymousUser()
        if uid:
            try:
                user = model.session.query(model.User).get(uid)
            except NoResultFound:
                pass

        add_user_authz_methods(user, self)
        return user


def main(global_config, **settings):
    """Constructs a WSGI application."""
    settings['paste_config'] = global_config

    ### Settings
    # Set up SQLAlchemy stuff
    engine = engine_from_config(settings, 'sqlalchemy.')
    model.initialize(engine, extension=ZopeTransactionExtension())

    # Misc other crap
    settings['rating_radius'] = int(settings['rating_radius'])
    settings['filestore_factory'] = filestore.get_storage_factory(settings)

    config = Configurator(
        settings=settings,
        root_factory=FloofRoot,
        authentication_policy=FloofAPIAuthnPolicy(),
        authorization_policy=ACLAuthorizationPolicy(),
        request_factory=FloofAPIRequest,
        session_factory=None,
    )

    floof.routing.configure_routing(config)
    config.scan(floof.api.views)

    app = config.make_wsgi_app()
    return app
