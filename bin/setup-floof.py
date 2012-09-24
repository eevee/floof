"""Setup the floof application"""
import logging
import os
import transaction
import sys

from alembic import command
from alembic.config import Config
from paste.deploy import appconfig
from sqlalchemy import engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from floof.lib.setup import generate_ca
from floof.lib.setup import populate_db
from floof import model

log = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] in ('-h', '--help'):
        print 'usage: python {0} config-file.ini#app-name alembic.ini'.format(sys.argv[0])
        sys.exit(0)

    ini_spec = os.path.abspath(sys.argv[1])
    alembic_ini_path = os.path.abspath(sys.argv[2])

    # Get paster to interpret the passed config file
    conf = appconfig('config:' + ini_spec)

    # Set up the SQLAlchemy environment
    model.initialize(
        engine_from_config(conf, 'sqlalchemy.'),
        conf,
        extension=ZopeTransactionExtension())

    populate_db(model.TableBase.metadata, model.session)
    alembic_cfg = Config(alembic_ini_path)
    command.stamp(alembic_cfg, 'head')
    generate_ca(conf)

    # XXX: This may be bad juju
    transaction.commit()
