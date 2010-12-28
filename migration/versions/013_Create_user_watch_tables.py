from sqlalchemy import *
from migrate import *

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint
TableBase = declarative_base()

# Old table stubs
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)


# New tables
class UserWatch(TableBase):
    __tablename__ = 'user_watches'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    other_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)
    watch_upload = Column(Boolean, nullable=False, index=True, default=False)
    watch_by = Column(Boolean, nullable=False, index=True, default=False)
    watch_for = Column(Boolean, nullable=False, index=True, default=False)
    watch_of = Column(Boolean, nullable=False, index=True, default=False)
    created_time = Column(DateTime, nullable=False, index=True)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    UserWatch.__table__.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    UserWatch.__table__.drop()
