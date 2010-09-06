"""Setup the floof application"""
import logging
import os.path

from floof.config.environment import load_environment
from floof.model import meta

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup floof here"""
    load_environment(conf.global_conf, conf.local_conf)

    ### DB stuff
    meta.metadata.bind = meta.engine

    _, conf_file = os.path.split(conf.filename)
    if conf_file == 'test.ini':
        # Drop all existing tables during a test
        meta.metadata.drop_all(checkfirst=True)

    # Create the tables if they don't already exist
    meta.metadata.create_all(checkfirst=True)
