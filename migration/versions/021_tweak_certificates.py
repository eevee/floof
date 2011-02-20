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

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

# Modified tables
class Certificate(TableBase):
    __tablename__ = 'certificates'
    id = Column(Integer, primary_key=True, nullable=False)
    serial = Column(Unicode, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_time = Column(TZDateTime, nullable=False)
    expiry_time = Column(TZDateTime, nullable=False)
    revoked = Column(Boolean, index=True, nullable=False, default=False)
    revoked_time = Column(TZDateTime)
    bits = Column(Integer, nullable=False)
    public_data = Column(String, nullable=False)
    private_data = Column(String)
    pkcs12_data = Column(LargeBinary)

ix_revoked = Index('ix_certificates_revoked', Certificate.__table__.c.revoked)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    ix_revoked.create()
    Certificate.__table__.c.private_data.drop()
    Certificate.__table__.c.pkcs12_data.drop()

def downgrade(migrate_engine):
    # Note that, as private keys cannot have a sensible default, this
    # function will NOT successfully transfer existing certificates,
    # but rather brake them.
    TableBase.metadata.bind = migrate_engine
    Certificate.__table__.c.pkcs12_data.create()
    Certificate.__table__.c.private_data.create()
    ix_revoked.drop()
