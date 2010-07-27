from sqlalchemy import *
from migrate import *
import migrate.changeset  # monkeypatches Column

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)
    media_type = Column(Enum(u'image', u'text', u'audio', u'video', name='artwork_media_type'), nullable=False)
    title = Column(Unicode(133), nullable=False)
    hash = Column(Unicode(256), nullable=False, unique=True, index=True)
    uploader_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, server_default='1')
    uploaded_time = Column(DateTime, nullable=False, index=True)
    created_time = Column(DateTime, nullable=False, index=True)
    original_filename = Column(Unicode(255), nullable=False)
    mime_type = Column(Unicode(255), nullable=False)
    file_size = Column(Integer, nullable=False)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    # This is dubious because it's NOT NULL; it'll just assign everything to
    # user 1, who ought to exist if there's any art at all.
    # Need to create it with a server default, then drop the default
    Artwork.__table__.c.uploader_user_id.create()
    Artwork.__table__.c.uploader_user_id.alter(server_default=None)

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Artwork.__table__.c.uploader_user_id.drop()
