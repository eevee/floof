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

    write_comment = Privilege(name=u'write_comment', description=u'Can post comments')

    Session = sessionmaker(bind=migrate_engine)()
    Session.add(write_comment)
    for role in Session.query(Role).filter(Role.name.in_([ u'user', u'admin' ])):
        Session.add(RolePrivilege(role_id=role.id, priv_id=write_comment.id))
    Session.commit()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    RolePrivilege.__table__.drop()
    Role.__table__.drop()
    Privilege.__table__.drop()
