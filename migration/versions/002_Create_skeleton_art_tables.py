from sqlalchemy import *
from migrate import *

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
    uploaded_time = Column(DateTime, nullable=False, index=True)
    created_time = Column(DateTime, nullable=False, index=True)
    original_filename = Column(Unicode(255), nullable=False)
    mime_type = Column(Unicode(255), nullable=False)
    file_size = Column(Integer, nullable=False)

class MediaImage(Artwork):
    __tablename__ = 'media_images'
    id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=False)
    height = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    frames = Column(Integer, nullable=True)
    length = Column(Time, nullable=True)
    quality = Column(Integer, nullable=True)

class MediaText(Artwork):
    __tablename__ = 'media_text'
    id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=False)
    words = Column(Integer, nullable=False)
    paragraphs = Column(Integer, nullable=False)


class UserArtwork(TableBase):
    __tablename__ = 'user_artwork'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=True)
    artwork_id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=True)
    relationship_type = Column(Enum(u'by', u'for', u'of', name='user_artwork_relationship_type'), primary_key=True, nullable=True)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Artwork.__table__.create()
    UserArtwork.__table__.create()
    MediaImage.__table__.create()
    MediaText.__table__.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    MediaText.__table__.drop()
    MediaImage.__table__.drop()
    UserArtwork.__table__.drop()
    Artwork.__table__.drop()
