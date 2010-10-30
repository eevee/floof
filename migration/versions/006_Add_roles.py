from sqlalchemy import *
from migrate import *

from sqlalchemy.orm import sessionmaker, relation
from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

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

Role.privileges = relation(Privilege, secondary=RolePrivilege.__table__)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    # Add tables and columns
    Role.__table__.create()
    Privilege.__table__.create()
    RolePrivilege.__table__.create()

    # Add canonical privileges and roles
    upload_art = Privilege(name=u'upload_art')
    admin_priv = Privilege(name=u'admin')
    base_user = Role(name=u'user', privileges=[upload_art])
    admin_user = Role(name=u'admin', privileges=[admin_priv, upload_art])

    Session = sessionmaker(bind=migrate_engine)()
    Session.add_all([base_user, admin_user])
    Session.commit()

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

    RolePrivilege.__table__.drop()
    Role.__table__.drop()
    Privilege.__table__.drop()
