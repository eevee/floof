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

# New tables
class Certificate(TableBase):
    __tablename__ = 'certificates'
    id = Column(Integer, primary_key=True, nullable=False)
    serial = Column(Unicode, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_time = Column(TZDateTime, nullable=False)
    expiry_time = Column(TZDateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_time = Column(TZDateTime)
    bits = Column(Integer, nullable=False)
    public_data = Column(String, nullable=False)
    private_data = Column(String, nullable=False)
    pkcs12_data = Column(LargeBinary, nullable=False)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Certificate.__table__.create()
    auth_method = User.__table__.c.auth_method
    auth_method.server_default = DefaultClause(u'openid_only')
    auth_method.type.create(migrate_engine)
    auth_method.create()
    auth_method.alter(server_default=None)

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Certificate.__table__.drop()
    auth_method = User.__table__.c.auth_method
    auth_method.drop()
    auth_method.type.drop(migrate_engine)
