"""The application's model objects"""
import datetime

from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation
from sqlalchemy.types import *

from floof.model import meta

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    meta.Session.configure(bind=engine)
    meta.engine = engine


TableBase = declarative_base()

### USERS

class AnonymousUser(object):
    """Fake not-logged-in user.

    Tests as false and generally responds correctly to User methods.
    """

    def __nonzero__(self):
        return False
    def __bool__(self):
        return False

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)

    @property
    def display_name(self):
        """Returns a flavory string that should be used to present this user.
        """

        return self.name

class IdentityURL(TableBase):
    __tablename__ = 'identity_urls'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    url = Column(Unicode(250), nullable=False, index=True, unique=True)


### ART

# TODO exif and png metadata -- do other formats have similar?  audio, video..  text?
class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)
    media_type = Column(Enum(u'image', u'text', u'audio', u'video', name='artwork_media_type'), nullable=False)
    title = Column(Unicode(133), nullable=False)
    hash = Column(Unicode(256), nullable=False, unique=True, index=True)
    uploaded_time = Column(DateTime, nullable=False, index=True, default=datetime.datetime.now)
    created_time = Column(DateTime, nullable=False, index=True, default=datetime.datetime.now)
    original_filename = Column(Unicode(255), nullable=False)
    mime_type = Column(Unicode(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    __mapper_args__ = {'polymorphic_on': media_type}

# Dynamic subclasses of the 'artwork' table for storing metadata for different
# types of media
class MediaImage(Artwork):
    __tablename__ = 'media_images'
    __mapper_args__ = {'polymorphic_identity': 'image'}
    id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=False)
    height = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    # animated only
    frames = Column(Integer, nullable=True)
    length = Column(Time, nullable=True)
    # jpeg only
    quality = Column(Integer, nullable=True)

class MediaText(Artwork):
    __tablename__ = 'media_text'
    __mapper_args__ = {'polymorphic_identity': 'text'}
    id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=False)
    words = Column(Integer, nullable=False)
    paragraphs = Column(Integer, nullable=False)


class UserArtwork(TableBase):
    __tablename__ = 'user_artwork'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=True)
    artwork_id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=True)
    relationship_type = Column(Enum(u'by', u'for', u'of', name='user_artwork_relationship_type'), primary_key=True, nullable=True)


### RELATIONS

# Users
IdentityURL.user = relation(User, backref='identity_urls')
