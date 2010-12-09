from sqlalchemy import *
from migrate import *
import migrate.changeset  # monkeypatches Column

from sqlalchemy.schema import DefaultClause
from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Old table stubs

class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

# New tables

class Tag(TableBase):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), unique=True)

class Label(TableBase):
    __tablename__ = 'labels'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    encapsulation = Column(Enum(u'public', u'private', name='labels_encapsulation'), nullable=False)

artwork_tags = Table('artwork_tags', TableBase.metadata,
    Column('artwork_id', Integer, ForeignKey('artwork.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
)

artwork_labels = Table('artwork_labels', TableBase.metadata,
    Column('artwork_id', Integer, ForeignKey('artwork.id'), primary_key=True),
    Column('label_id', Integer, ForeignKey('labels.id'), primary_key=True),
)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    Tag.__table__.create()
    artwork_tags.create()

    Label.__table__.create()
    artwork_labels.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    artwork_labels.create()
    Label.__table__.create()

    artwork_tags.create()
    Tag.__table__.create()
