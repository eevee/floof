"""Add show_art_scores to users

Revision ID: 1a0f2d288b26
Revises: 53bff2c5077d
Create Date: 2012-10-08 04:44:22.701137

"""

# revision identifiers, used by Alembic.
revision = '1a0f2d288b26'
down_revision = '53bff2c5077d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


def upgrade():
    op.add_column('users', sa.Column('show_art_scores', sa.Boolean()))

    users = table('users',
        column('id', sa.Integer()),
        column('show_art_scores', sa.Boolean()),
    )
    op.execute(
        users.update().values({'show_art_scores': False})
    )
    op.alter_column('users', 'show_art_scores',
       existing_type=sa.Boolean(),
       nullable=False)


def downgrade():
    op.drop_column('users', 'show_art_scores')
