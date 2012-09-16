"""remove relationship types

Revision ID: 46d6b7d546c
Revises: 310d62d88dc3
Create Date: 2012-09-16 13:35:24.700637

"""

# revision identifiers, used by Alembic.
revision = '46d6b7d546c'
down_revision = '10dae4dda9d4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.sql import table, column
from sqlalchemy.types import Enum, Integer, String


def upgrade():
    user_artwork = table('user_artwork',
        column('user_id', Integer),
        column('artwork_id', Integer),
        column('relationship_type', String),  # little white lie
    )
    op.execute(
        user_artwork.delete().where(
            user_artwork.c.relationship_type != op.inline_literal('by'))
    )

    op.drop_column('user_artwork', 'relationship_type')

    op.execute('DROP TYPE user_artwork_relationship_type')

    # Dropping the column also drops the primary key, so...
    op.execute('ALTER TABLE user_artwork ADD PRIMARY KEY (user_id, artwork_id)')

    # Create indices too
    op.create_index('ix_user_artwork_user_id', 'user_artwork', ['user_id'])
    op.create_index('ix_user_artwork_artwork_id', 'user_artwork', ['artwork_id'])


def downgrade():
    enum_type = Enum(u'by', u'for', u'of', name='user_artwork_relationship_type')
    enum_type.create(bind=op.get_bind())

    op.add_column('user_artwork',
        Column('relationship_type',
            enum_type,
            primary_key=True,
            nullable=False,
            server_default=op.inline_literal('by')))

    op.execute('ALTER TABLE user_artwork DROP CONSTRAINT user_artwork_pkey')
    op.execute('ALTER TABLE user_artwork ADD PRIMARY KEY (user_id, artwork_id, relationship_type)')

    op.drop_index('ix_user_artwork_user_id')
    op.drop_index('ix_user_artwork_artwork_id')
