"""Migrated to Dirichlet scoring for art ratings.

Revision ID: 53bff2c5077d
Revises: 46d6b7d546c
Create Date: 2012-09-28 10:40:49.371952

"""

# revision identifiers, used by Alembic.
revision = '53bff2c5077d'
down_revision = '46d6b7d546c'

import sys

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.types import Integer, Float


def upgrade():
    op.drop_column('artwork', u'rating_sum')

    artwork = table('artwork',
        column('id', Integer),
        column('rating_score', Float),
    )
    op.execute(
        artwork.update().\
                where(artwork.c.rating_score==None).\
                values({'rating_score': 0})
    )
    op.alter_column('artwork', 'rating_score',
       existing_type=Float(),
       nullable=False)

    op.alter_column('artwork_ratings', u'rating',
       existing_type=Float(),
       type_=Integer(),
       existing_nullable=False)

    print >> sys.stderr, """
You have migrated to Dirichlet scoring but your artwork scores have not
been updated.  You will need to choose a global prior, set it in your
config.ini, then run:

python bin/rescore.py config.ini#floof-prod

(adjust the argument to fit your config file).
"""


def downgrade():
    op.alter_column('artwork_ratings', u'rating',
       existing_type=Integer(),
       type_=Float(),
       existing_nullable=False)

    op.alter_column('artwork', 'rating_score',
       existing_type=Float(),
       nullable=True)

    op.add_column('artwork',
        sa.Column(u'rating_sum',
            Float(),
            nullable=False,
            server_default='0'))
    op.alter_column('artwork', 'rating_sum', server_default=None)

    print >> sys.stderr, """
You have migrated from Dirichlet to Wilson scoring but your artwork
scores have not been migrated.  You will need to go about this manually.
"""
