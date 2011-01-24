from sqlalchemy import *
from migrate import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from floof.model.types import IPAddr

TableBase = declarative_base()

# Stub tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

class Privilege(TableBase):
    __tablename__ = 'privileges'
    id = Column(Integer, primary_key=True, nullable=False)

# New tables
class Log(TableBase):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    visibility = Column(Enum(u'public', u'admin'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    logger = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    url = Column(Unicode)
    ipaddr = Column(IPAddr)
    target_user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(Unicode, nullable=False)
    reason = Column(Unicode)

log_privileges = Table('log_privileges', TableBase.metadata,
    Column('log_id', Integer, ForeignKey('logs.id'), primary_key=True, nullable=False),
    Column('priv_id', Integer, ForeignKey('privileges.id'), primary_key=True, nullable=False),
    useexisting=True,
)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Log.__table__.create()
    log_privileges.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    log_privileges.drop()
    Log.__table__.drop()

