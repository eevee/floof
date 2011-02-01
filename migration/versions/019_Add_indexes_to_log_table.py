from sqlalchemy import *
from migrate import *

from floof.model import now
from floof.model.types import IPAddr

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Stub tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

class Log(TableBase):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=now)
    visibility = Column(Enum(u'public', u'admin', name='logs_visibility'), nullable=False)
    logger = Column(String, nullable=False)
    level = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    url = Column(Unicode)
    ipaddr = Column(IPAddr)
    target_user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(Unicode, nullable=False)
    reason = Column(Unicode)

ix_timestamp = Index('ix_logs_timestamp', Log.__table__.c.timestamp)
ix_level = Index('ix_logs_level', Log.__table__.c.level)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    ix_timestamp.create()
    ix_level.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    ix_timestamp.drop()
    ix_level.drop()
