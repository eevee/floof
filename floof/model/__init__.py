"""The application's model objects"""
import datetime
import pytz
import re

from sqlalchemy import Column, ForeignKey, MetaData, Table, and_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, class_mapper, relation
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import object_session
from sqlalchemy.schema import UniqueConstraint
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

### CORE

class Resource(TableBase):
    """Art and users and perhaps other things have-a discussion, which is fine
    and dandy, but it means the discussion can't easily find its way back to
    the "discussee": there are multiple backrefs to check.

    The solution is this semi-hacky middle table that remembers the discussee's
    table name, and a dose of SQLA magic to make it all invisible.
    Art/User/etc. can still get directly to the discussion and doesn't need
    this table, but going backwards is much easier.

    The table is named "Resource" with the intention that it may later perform
    other duties, such as allowing joins from tags to anything, or facilitating
    global full-text search, or whatever.

    Kudos to zzzeek for the idea and example implementation:
    http://techspot.zzzeek.org/?p=13
    """
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(Enum(u'artwork', u'users', name='resources_type'), nullable=False)

    @property
    def member(self):
        return getattr(self, '_backref_%s' % self.type)

def make_resource_type(cls):
    """For table-classes that are resources.  Installs a backref on Resource
    that finds the original class.

    Also adds a 'discussion' association-proxy shortcut.
    """

    mapper = class_mapper(cls)
    table = mapper.local_table
    mapper.add_property('resource', relation(
        Resource, backref=backref('_backref_%s' % table.name, uselist=False)
    ))

    # Attach a 'discussion' shortcut
    for resource_property in ('discussion',):
        setattr(cls, resource_property,
            association_proxy('resource', resource_property))

    return cls


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
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
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

        priv = object_session(self).query(Privilege) \
            .filter_by(name=permission).one()

        return priv in self.role.privileges

    @property
    def display_name(self):
        """Returns a flavory string that should be used to present this user.
        """

        return self.name

    @property
    def profile(self):
        """Returns the user's profile, if they have one.

        This would use ext.association_proxy, but that doesn't play nicely if
        the object to proxy is None.
        """
        if self._profile is None:
            return None
        return self._profile.content

    @profile.setter
    def profile(self, value):
        if self._profile is None:
            self._profile = UserProfile()
        self._profile.content = value

class IdentityURL(TableBase):
    __tablename__ = 'identity_urls'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    url = Column(Unicode(250), nullable=False, index=True, unique=True)

class UserWatch(TableBase):
    __tablename__ = 'user_watches'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    other_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    watch_upload = Column(Boolean, nullable=False, index=True, default=False)
    watch_by = Column(Boolean, nullable=False, index=True, default=False)
    watch_for = Column(Boolean, nullable=False, index=True, default=False)
    watch_of = Column(Boolean, nullable=False, index=True, default=False)
    created_time = Column(TZDateTime, nullable=False, index=True, default=now)


### ART

# TODO exif and png metadata -- do other formats have similar?  audio, video..  text?
class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
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

    @property
    def resource_title(self):
        return self.title or 'Untitled'

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


user_artwork_types = (u'by', u'for', u'of')
class UserArtwork(TableBase):
    __tablename__ = 'user_artwork'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=True)
    artwork_id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=True)
    relationship_type = Column(Enum(*user_artwork_types, name='user_artwork_relationship_type'), primary_key=True, nullable=True)


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
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    comment_count = Column(Integer, nullable=False, default=0)

class Comment(TableBase):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)
    posted_time = Column(TZDateTime, nullable=False, index=True, default=now)
    author_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # Nested set threading; Google it
    left = Column(Integer, index=True, nullable=False)
    right = Column(Integer, index=True, nullable=False)
    content = Column(UnicodeText(4096), nullable=False)

    @property
    def ancestors_query(self):
        """Returns a query that will fetch all comments somewhere above this
        one, in correct linear order.
        """
        # Ancestors are any comments whose left and right contain this
        # comment's left
        return object_session(self).query(Comment) \
            .with_parent(self.discussion) \
            .filter(Comment.left < self.left) \
            .filter(Comment.right > self.right) \
            .order_by(Comment.left.asc())

    @property
    def descendants_query(self):
        """Returns a query that will fetch all comments nested below this one,
        including this one itself, in correct linear order.
        """
        # Descendants are any comments with a left (or right) between
        # comment.left and comment.right
        return object_session(self).query(Comment) \
            .with_parent(self.discussion) \
            .filter(Comment.left.between(self.left, self.right)) \
            .order_by(Comment.left.asc())


### PROFILES

class UserProfile(TableBase):
    __tablename__ = 'user_profiles'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    content = Column(Unicode, nullable=True)

class UserProfileRevision(TableBase):
    __tablename__ = 'user_profile_revisions'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    updated_at = Column(DateTime, primary_key=True, nullable=False, default=now)
    updated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Unicode, nullable=True)


### TAGS

def get_or_create_tag(name):
    try:
        return meta.Session.query(Tag).filter_by(name=name).one()
    except NoResultFound:
        return Tag(name)

class Tag(TableBase):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), unique=True)

    def __init__(self, name):
        self.name = name

class Label(TableBase):
    __tablename__ = 'labels'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    encapsulation = Column(Enum(u'public', u'private', name='labels_encapsulation'), nullable=False)

artwork_tags = Table('artwork_tags', meta.metadata,
    Column('artwork_id', Integer, ForeignKey('artwork.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
)

artwork_labels = Table('artwork_labels', meta.metadata,
    Column('artwork_id', Integer, ForeignKey('artwork.id'), primary_key=True),
    Column('label_id', Integer, ForeignKey('labels.id'), primary_key=True),
)


### RELATIONS
# TODO: For user/user and user/art relations, it would be nice to have SQLA represent them as a dict of lists.
# See: http://www.sqlalchemy.org/docs/orm/collections.html#instrumentation-and-custom-types

make_resource_type(User)
make_resource_type(Artwork)

# Users
IdentityURL.user = relation(User, backref='identity_urls')
User.watches = relation(UserWatch,
    primaryjoin=User.id==UserWatch.user_id,
    backref='user')
User.inverse_watches = relation(UserWatch,
    primaryjoin=User.id==UserWatch.other_user_id,
    backref='other_user')


# Profiles
UserProfile.user = relation(User, uselist=False, backref=backref('_profile', uselist=False))
UserProfileRevision.user = relation(User, uselist=False, backref='profile_revisions',
    foreign_keys=[UserProfileRevision.user_id],
    primaryjoin=UserProfileRevision.user_id == User.id)
UserProfileRevision.updated_by = relation(User, uselist=False,
    foreign_keys=[UserProfileRevision.updated_by_id],
    primaryjoin=UserProfileRevision.updated_by_id == User.id)


# Art
#Artwork.discussion = relation(Discussion, backref='artwork')
Artwork.tag_objs = relation(Tag, backref='artwork', secondary=artwork_tags)
Artwork.tags = association_proxy('tag_objs', 'name', creator=get_or_create_tag)
Artwork.uploader = relation(User, backref='uploaded_artwork')
Artwork.user_artwork = relation(UserArtwork, backref='artwork')

#User.discussion = relation(Discussion, backref='user')
User.user_artwork = relation(UserArtwork, backref='user')

# Permissions
User.role = relation(Role, uselist=False, backref='users')
Role.privileges = relation(Privilege, secondary=RolePrivilege.__table__)

# Comments
Resource.discussion = relation(Discussion, uselist=False, backref='resource')

Comment.author = relation(User, backref='comments')

Discussion.comments = relation(Comment, order_by=Comment.left.asc(), backref='discussion')

# Tags & Labels
Label.user = relation(User, backref='labels')
Label.artwork = relation(Artwork, secondary=artwork_labels)
