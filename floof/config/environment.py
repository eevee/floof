"""Pylons environment configuration"""
import os, os.path
import subprocess

from mako.lookup import TemplateLookup
from paste.deploy.converters import asbool
import pylons
from pylons.configuration import PylonsConfig
from pylons.error import handle_mako_error
from sqlalchemy import engine_from_config

import floof.lib.app_globals as app_globals
import floof.lib.debugging
import floof.lib.helpers
from floof.config.routing import make_map
from floof.model import filestore, init_model

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config = PylonsConfig()
    config.init_app(global_conf, app_conf, package='floof', paths=paths)

    config['routes.map'] = make_map(config)
    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.h'] = floof.lib.helpers
    pylons.cache._push_object(config['pylons.app_globals'].cache)

    # Create the Mako TemplateLookup, with the default auto-escaping
    config['pylons.app_globals'].mako_lookup = TemplateLookup(
        directories=paths['templates'],
        error_handler=handle_mako_error,
        module_directory=os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding='utf-8', default_filters=['escape'],
        imports=['from webhelpers.html import escape'])

    # Setup SQLAlchemy database engine
    # Proxy class is just to record query time; in debugging mode, it also
    # tracks every query
    config['super_debug'] = asbool(config.get('super_debug', False))
    if config['super_debug']:
        sqla_proxy = floof.lib.debugging.SQLAQueryLogProxy()
    else:
        sqla_proxy = floof.lib.debugging.SQLATimerProxy()
    config['super_debug.sqlalchemy_proxy'] = sqla_proxy
    engine = engine_from_config(config, 'sqlalchemy.', proxy=sqla_proxy)
    init_model(engine)

    # Compile stylesheets with Sass
    # This env var is only set from a convenient launcher script
    if 'FLOOF_SKIP_SASS_COMPILATION' not in os.environ:
        sass_paths = u':'.join((
            os.path.join(root, 'sass'),
            os.path.join(root, 'public', 'css'),
        ))
        subprocess.Popen(['sass',
            '--scss',
            '--style', 'compressed',
            '--stop-on-error',
            '--update', sass_paths,
        ]).wait()

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)

    # Create file storage object and stick it back in the config
    storage = filestore.get_storage(config)
    config['filestore'] = storage

    return config
