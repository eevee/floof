from sqlalchemy import *
import sqlalchemy.exc
from migrate import *

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

from migrate.changeset import schema  # monkeypatches columns

# Stubs for old tables

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

class Artwork(TableBase):
    __tablename__ = 'Artwork'
    id = Column(Integer, primary_key=True, nullable=False)

# Old tables

user_artwork_types = (u'by', u'for', u'of')
class UserArtwork(TableBase):
    __tablename__ = 'user_artwork'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=True)
    artwork_id = Column(Integer, ForeignKey('artwork.id'), primary_key=True, nullable=True)
    relationship_type = Column(Enum(*user_artwork_types, name='user_artwork_relationship_type'), primary_key=True, nullable=False)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    UserArtwork.__table__.c.user_id.alter(nullable=False)
    UserArtwork.__table__.c.artwork_id.alter(nullable=False)
    UserArtwork.__table__.c.relationship_type.alter(nullable=False)

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    # Primary keys can't actually be NULLable in pg, so this will raise
    try:
        UserArtwork.__table__.c.user_id.alter(nullable=True)
        UserArtwork.__table__.c.artwork_id.alter(nullable=True)
        UserArtwork.__table__.c.relationship_type.alter(nullable=True)
    except sqlalchemy.exc.ProgrammingError:
        pass
