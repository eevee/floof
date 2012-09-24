import os

from paste.deploy import appconfig
from sqlalchemy import engine_from_config

from floof import model


def bootstrap_floof(ini_spec):
    """Interpret the config file and load the DB."""

    # Get paster to interpret the passed config file
    ini_spec = os.path.abspath(ini_spec)
    settings = appconfig('config:' + ini_spec)

    # Set up the SQLAlchemy environment
    model.initialize(
        engine_from_config(settings, 'sqlalchemy.'),
        settings,
    )

    return settings
