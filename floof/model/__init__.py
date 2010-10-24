"""The application's model objects"""
import datetime
import pytz
import re

from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation
from sqlalchemy.types import *
from floof.model.types import *

from floof.model import meta

def now():
    return datetime.datetime.now(pytz.utc)

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    meta.Session.configure(bind=engine)
    meta.engine = engine


TableBase = declarative_base(metadata=meta.metadata)

### USERS

class AnonymousUser(object):
    """Fake not-logged-in user.

    Tests as false and generally responds correctly to User methods.
    """

    def __nonzero__(self):
        return False
    def __bool__(self):
        return False

    def localtime(self, dt):
        """Anonymous users can suffer UTC."""
        return dt

    def can(self, permission):
        """Anonymous users aren't allowed to do anything that needs explicit
        permission.
        """
        return False

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)
    timezone = Column(Timezone, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    def localtime(self, dt):
        """Return a datetime localized to this user's preferred timezone."""
        if self.timezone is None:
            return dt
        return dt.astimezone(self.timezone)

    def can(self, permission):
        """Returns True iff this user has the named privilege."""
        if not self.role:
            return False
        for priv in self.role.privileges:
            if priv.name == permission:
                return True
        return False

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
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)
    media_type = Column(Enum(u'image', u'text', u'audio', u'video', name='artwork_media_type'), nullable=False)
    title = Column(Unicode(133), nullable=False)
    hash = Column(Unicode(256), nullable=False, unique=True, index=True)
    uploader_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploaded_time = Column(TZDateTime, nullable=False, index=True, default=now)
    created_time = Column(TZDateTime, nullable=False, index=True, default=now)
    original_filename = Column(Unicode(255), nullable=False)
    mime_type = Column(Unicode(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    __mapper_args__ = {'polymorphic_on': media_type}

# Dynamic subclasses of the 'artwork' table for storing metadata for different
# types of media
class MediaImage(Artwork):
    __tablename__ = 'media_images'
    __mapper_args__ = {'polymorphic_identity': u'image'}
    id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=False)
    height = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    number_of_colors = Column(Integer, nullable=False)
    # animated only
    frames = Column(Integer, nullable=True)
    length = Column(Time, nullable=True)
    # jpeg only
    quality = Column(Integer, nullable=True)

class MediaText(Artwork):
    __tablename__ = 'media_text'
    __mapper_args__ = {'polymorphic_identity': u'text'}
    id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=False)
    words = Column(Integer, nullable=False)
    paragraphs = Column(Integer, nullable=False)


class UserArtwork(TableBase):
    __tablename__ = 'user_artwork'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=True)
    artwork_id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=True)
    relationship_type = Column(Enum(u'by', u'for', u'of', name='user_artwork_relationship_type'), primary_key=True, nullable=True)


### PERMISSIONS

class Role(TableBase):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

class Privilege(TableBase):
    __tablename__ = 'privileges'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

class RolePrivilege(TableBase):
    __tablename__ = 'role_privileges'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, nullable=False)
    priv_id = Column(Integer, ForeignKey('privileges.id'), primary_key=True, nullable=False)


### COMMENTS

class Discussion(TableBase):
    __tablename__ = 'discussions'
    id = Column(Integer, primary_key=True, nullable=False)
    comment_count = Column(Integer, nullable=False, default=0)

class Comment(TableBase):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)
    posted_time = Column(DateTime, nullable=False, index=True, default=datetime.datetime.now)
    author_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # Nested set threading; Google it
    left = Column(Integer, index=True, nullable=False)
    right = Column(Integer, index=True, nullable=False)
    content = Column(UnicodeText(4096), nullable=False)


### RELATIONS

# Users
IdentityURL.user = relation(User, backref='identity_urls')


# Art
Artwork.discussion = relation(Discussion, backref='artwork')
Artwork.uploader = relation(User, backref='uploaded_artwork')
Artwork.user_artwork = relation(UserArtwork, backref='artwork')

User.discussion = relation(Discussion, backref='user')
User.user_artwork = relation(UserArtwork, backref='user')

# Permissions
User.role = relation(Role, uselist=False, backref='users')
Role.privileges = relation(Privilege, secondary=RolePrivilege.__table__)

# Comments
Comment.author = relation(User, backref='comments')

Discussion.comments = relation(Comment, order_by=Comment.left.asc(), backref='discussion')
