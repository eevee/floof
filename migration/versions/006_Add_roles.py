from sqlalchemy import *
from migrate import *
from floof.model.types import Timezone

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)
    timezone = Column(Timezone, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)

class Role(TableBase):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

class Privilege(TableBase):
    __tablename__ = 'privileges'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

class RolePrivilege(TableBase):
    __tablename__ = 'role_privileges'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, nullable=False)
    priv_id = Column(Integer, ForeignKey('privileges.id'), primary_key=True, nullable=False)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    Role.__table__.create()
    Privilege.__table__.create()
    RolePrivilege.__table__.create()
    User.__table__.c.role_id.create()

    # Add canonical privileges and roles
    upload_art = Privilege(name=u'upload_art', description=u'Can upload art')
    admin_priv = Privilege(name=u'admin', description=u'Can administrate')
    base_user = Role(name=u'user', description=u'Basic user', privileges=[upload_art])
    admin_user = Role(name=u'admin', description=u'Administrator', privileges=[admin_priv, upload_art])

    Session = sessionmaker(bind=migrate_engine)()
    Session.add_all([base_user, admin_user])
    Session.commit()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    User.__table__.c.role_id.drop()
    RolePrivilege.__table__.drop()
    Role.__table__.drop()
    Privilege.__table__.drop()
