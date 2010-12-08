from sqlalchemy import *
from migrate import *
import migrate.changeset  # monkeypatches Column

from sqlalchemy.schema import DefaultClause
from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Old table stubs

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

# New tables

class UserProfile(TableBase):
    __tablename__ = 'user_profiles'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    content = Column(Unicode, nullable=True)

class UserProfileRevision(TableBase):
    __tablename__ = 'user_profile_revisions'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    updated_at = Column(DateTime, primary_key=True, nullable=False)
    updated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Unicode, nullable=True)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    UserProfile.__table__.create()
    UserProfileRevision.__table__.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    UserProfileRevision.__table__.drop()
    UserProfile.__table__.drop()
