"""Setup the floof application"""
import logging

from floof.config.environment import load_environment
from floof.model import meta

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup floof here"""
    load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    meta.metadata.create_all(bind=meta.engine)
