from sqlalchemy import *
from migrate import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from floof.model.types import Timezone, TZDateTime

TableBase = declarative_base()

# Stub tables
class Role(TableBase):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, nullable=False)

# Modified tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)
    timezone = Column(Timezone, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    auth_method = Column(Enum(
        u'cert_only',
        u'openid_only',
        u'cert_or_openid',
        u'cert_and_openid',
        name='user_auth_method'), nullable=False)
    cert_auth = Column(Enum(
        u'disabled',
        u'allowed',
        u'sensitive_required',
        u'required',
        name='user_cert_auth'), nullable=False)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    cert_auth = User.__table__.c.cert_auth
    cert_auth.server_default = DefaultClause(u'disabled')
    cert_auth.type.create(migrate_engine)
    cert_auth.create()
    cert_auth.alter(server_default=None)
    auth_method = User.__table__.c.auth_method
    auth_method.drop()
    auth_method.type.drop(migrate_engine)

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    auth_method = User.__table__.c.auth_method
    auth_method.server_default = DefaultClause(u'openid_only')
    auth_method.type.create(migrate_engine)
    auth_method.create()
    auth_method.alter(server_default=None)
    cert_auth = User.__table__.c.cert_auth
    cert_auth.drop()
    cert_auth.type.drop(migrate_engine)
