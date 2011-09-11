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
from floof.model import meta
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
    engine = engine_from_config(conf, 'sqlalchemy.')
    meta.Session.configure(bind=engine, extension=ZopeTransactionExtension())
    model.TableBase.metadata.bind = engine

    populate_db(meta)
    generate_ca(conf, meta)

    # XXX: This may be bad juju
    transaction.commit()
