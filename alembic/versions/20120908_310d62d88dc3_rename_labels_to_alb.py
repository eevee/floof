"""rename labels to albums

Revision ID: 310d62d88dc3
Revises: None
Create Date: 2012-09-08 16:44:09.602392

"""

# revision identifiers, used by Alembic.
revision = '310d62d88dc3'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('artwork_labels', 'artwork_albums')
    op.alter_column('artwork_albums', 'label_id', name='album_id')

    op.rename_table('labels', 'albums')

    # Bah, there's no built-in support for this yet, so do it manually
    op.execute('ALTER TYPE labels_encapsulation RENAME TO albums_encapsulation')


def downgrade():
    op.execute('ALTER TYPE albums_encapsulation RENAME TO labels_encapsulation')

    op.rename_table('albums', 'labels')

    op.alter_column('artwork_labels', 'album_id', name='label_id')
    op.rename_table('artwork_albums', 'artwork_labels')
