"""Setup the floof application"""
import logging
import os
import transaction
import sys

from paste.deploy import appconfig
from sqlalchemy import engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from floof.lib.setup import generate_ca
from floof.lib.setup import populate_db
from floof import model

log = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print 'usage: python {0} config-file.ini#app-name'.format(sys.argv[0])
        sys.exit(0)

    # Get paster to interpret the passed config file
    ini_spec = os.path.abspath(sys.argv[1])
    conf = appconfig('config:' + ini_spec)

    # Set up the SQLAlchemy environment
    model.initialize(
        engine_from_config(conf, 'sqlalchemy.'),
        extension=ZopeTransactionExtension())

    populate_db(model.TableBase.metadata, model.session)
    generate_ca(conf)

    # XXX: This may be bad juju
    transaction.commit()
