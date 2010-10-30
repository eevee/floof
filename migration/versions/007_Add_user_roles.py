from sqlalchemy import *
from migrate import *
from floof.model.types import Timezone

from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import DefaultClause
from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)
    timezone = Column(Timezone, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

class Role(TableBase):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    Session = sessionmaker(bind=migrate_engine)()
    base_user_id, = Session.query(Role.id).filter_by(name=u'user').one()
    Session.rollback()

    # Create with a useful server default so it'll be populated, then remove
    # the default
    role_id = User.__table__.c.role_id
    role_id.server_default = DefaultClause(str(base_user_id))
    role_id.create()
    role_id.alter(server_default=None)

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    User.__table__.c.role_id.drop()
