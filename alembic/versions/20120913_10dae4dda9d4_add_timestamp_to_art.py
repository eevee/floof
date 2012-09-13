"""add timestamp to art

Revision ID: 10dae4dda9d4
Revises: 310d62d88dc3
Create Date: 2012-09-13 06:52:45.984499

"""

# revision identifiers, used by Alembic.
revision = '10dae4dda9d4'
down_revision = '310d62d88dc3'

from alembic import op
import sqlalchemy as sa

from floof.model.types import TZDateTime


def upgrade():
    op.add_column('artwork_ratings',
        sa.Column('timestamp', TZDateTime, nullable=False, server_default=sa.func.now()))
    op.alter_column('artwork_ratings', 'timestamp', server_default=None)
    op.create_index('ix_artwork_ratings_timestamp', 'artwork_ratings', ['timestamp'])


def downgrade():
    op.drop_column('artwork_ratings', 'timestamp')
