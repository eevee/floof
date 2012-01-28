from sqlalchemy import *
from migrate import *

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()


# Stub tables
class MediaImage(TableBase):
    __tablename__ = 'media_images'
    id = Column(Integer, primary_key=True, nullable=False)


# Modified tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    avatar_id = Column(Integer, ForeignKey('avatars.id'), nullable=True)


# New tables
class Avatar(TableBase):
    __tablename__ = 'avatars'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # NB: it is valid to have multiple avatars with the same key
    hash = Column(Unicode(256), nullable=False, unique=False, index=True)
    mime_type = Column(Unicode(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    derived_image_id = Column(Integer, ForeignKey('media_images.id'), nullable=True)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Avatar.__table__.create()
    User.__table__.c.avatar_id.create()


def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    User.__table__.c.avatar_id.drop()
    Avatar.__table__.drop()
