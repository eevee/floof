from sqlalchemy import *
from migrate import *

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()


# Stub tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)


# New tables
class IdentityEmail(TableBase):
    __tablename__ = 'identity_emails'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    email = Column(Unicode(256), nullable=False, index=True, unique=True)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    IdentityEmail.__table__.create()


def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    IdentityEmail.__table__.drop()
