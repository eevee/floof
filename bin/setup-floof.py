"""Setup the floof application"""
import logging
import os
import sys

from alembic import command
from alembic.config import Config

from floof.lib.setup import generate_ca, populate_db
from floof import model

from bootstrap import bootstrap_floof

log = logging.getLogger(__name__)


if len(sys.argv) < 3 or sys.argv[1] in ('-h', '--help'):
    print 'usage: python {0} config-file.ini#app-name alembic.ini'.format(sys.argv[0])
    sys.exit(1)

settings = bootstrap_floof(sys.argv[1])
alembic_ini_path = os.path.abspath(sys.argv[2])

populate_db(model.TableBase.metadata, model.session)
alembic_cfg = Config(alembic_ini_path)
command.stamp(alembic_cfg, 'head')
generate_ca(settings)

model.session.commit()
