from sqlalchemy import *
from migrate import *

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relation
TableBase = declarative_base()

# Stub tables
class Role(TableBase):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)

# Modified tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

class Log(TableBase):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    privileges = Column(Unicode)

# New tables
class UserRole(TableBase):
    __tablename__ = 'user_roles'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, nullable=False)

# Deleted tables
class Privilege(TableBase):
    __tablename__ = 'privileges'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

class RolePrivilege(TableBase):
    __tablename__ = 'role_privileges'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, nullable=False)
    priv_id = Column(Integer, ForeignKey('privileges.id'), primary_key=True, nullable=False)


class LogPrivilege(TableBase):
    __tablename__ = 'log_privileges'
    log_id = Column(Integer, ForeignKey('logs.id'), primary_key=True, nullable=False)
    priv_id = Column(Integer, ForeignKey('privileges.id'), primary_key=True, nullable=False)


Role.privileges = relation(Privilege, secondary=RolePrivilege.__table__)
User.role = relation(Role, innerjoin=True, backref='users')
User.roles = relation(Role, UserRole.__table__)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    LogPrivilege.__table__.drop()
    RolePrivilege.__table__.drop()
    Privilege.__table__.drop()
    UserRole.__table__.create()
    Log.__table__.c.privileges.create()

    Session = sessionmaker(bind=migrate_engine)()

    user_role = Session.query(Role).filter_by(name=u'user').one()
    admin_role = Session.query(Role).filter_by(name=u'admin').one()

    for user in Session.query(User).all():
        user.roles.append(user_role)
    for user in Session.query(User).filter_by(role=admin_role).all():
        user.roles.append(admin_role)

    Session.commit()

    User.__table__.c.role_id.drop()

def downgrade(migrate_engine):
    # XXX will drop everyone to just the basic user role

    TableBase.metadata.bind = migrate_engine
    Session = sessionmaker(bind=migrate_engine)()

    base_user_id, = Session.query(Role.id).filter_by(name=u'user').one()
    Session.rollback()
    role_id = User.__table__.c.role_id
    role_id.server_default = DefaultClause(str(base_user_id))
    role_id.create()
    role_id.alter(server_default=None)

    Log.__table__.c.privileges.drop()
    UserRole.__table__.drop()

    Privilege.__table__.create()
    RolePrivilege.__table__.create()
    LogPrivilege.__table__.create()

    # Add canonical privileges
    privileges = [
        Privilege(name=name, description=description)
        for name, description in [
            (u'auth.certificates',  u'Can manage own client certificates'),
            (u'auth.method',        u'Can manage own authentication method'),
            (u'auth.openid',        u'Can manage own OpenID URLs'),
            (u'art.upload',         u'Can upload art'),
            (u'art.rate',           u'Can rate art'),
            (u'comments.add',       u'Can post comments'),
            (u'tags.add',           u'Can add tags with no restrictions'),
            (u'tags.remove',        u'Can remove tags with no restrictions'),
            (u'admin.view',         u'Can view administrative tools/panel'),
        ]
    ]

    user_role = Session.query(Role).filter_by(name=u'user').one()
    admin_role = Session.query(Role).filter_by(name=u'admin').one()
    for priv in privileges:
        admin_role.privileges.append(priv)
        if not priv.name.startswith('admin.'):
            user_role.privileges.append(priv)

    Session.commit()
