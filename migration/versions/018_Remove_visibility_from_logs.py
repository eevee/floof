from sqlalchemy import *
from migrate import *
from floof.model import now
from floof.model.types import IPAddr

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import DefaultClause
TableBase = declarative_base()

# Stub tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

class Log(TableBase):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=now)
    visibility = Column(Enum(u'public', u'admin', name='logs_visibility'), nullable=False)
    logger = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    url = Column(Unicode)
    ipaddr = Column(IPAddr)
    target_user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(Unicode, nullable=False)
    reason = Column(Unicode)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Log.__table__.c.visibility.drop()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    visibility = Log.__table__.c.visibility
    visibility.server_default = DefaultClause('admin')
    visibility.create()
    visibility.alter(server_default=None)
