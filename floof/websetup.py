"""Setup the floof application"""
import logging
import os.path

import pylons.test

from floof.config.environment import load_environment
from floof.model import meta
from floof import model

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup floof here"""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
            load_environment(conf.global_conf, conf.local_conf)

    ### DB stuff
    meta.metadata.bind = meta.engine

    _, conf_file = os.path.split(conf.filename)
    if conf_file == 'test.ini':
        # Drop all existing tables during a test
        meta.metadata.drop_all(checkfirst=True)

    # Create the tables if they don't already exist
    meta.metadata.create_all(checkfirst=True)

    # Add canonical privileges and roles
    upload_art = model.Privilege(name=u'upload_art', description=u'Can upload art')
    admin_priv = model.Privilege(name=u'admin', description=u'Can administrate')
    base_user = model.Role(name=u'user', description=u'Basic user', privileges=[upload_art])
    admin_user = model.Role(name=u'admin', description=u'Administrator', privileges=[admin_priv, upload_art])
    meta.Session.add_all([base_user, admin_user])
    meta.Session.commit()
