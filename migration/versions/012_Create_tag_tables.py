from sqlalchemy import *
from migrate import *
import migrate.changeset  # monkeypatches Column

from sqlalchemy.orm import sessionmaker, relation
from sqlalchemy.schema import DefaultClause
from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Old table stubs

class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)

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

# New tables

class Tag(TableBase):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), unique=True)

class Label(TableBase):
    __tablename__ = 'labels'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    encapsulation = Column(Enum(u'public', u'private', name='labels_encapsulation'), nullable=False)

artwork_tags = Table('artwork_tags', TableBase.metadata,
    Column('artwork_id', Integer, ForeignKey('artwork.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
)

artwork_labels = Table('artwork_labels', TableBase.metadata,
    Column('artwork_id', Integer, ForeignKey('artwork.id'), primary_key=True),
    Column('label_id', Integer, ForeignKey('labels.id'), primary_key=True),
)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    Tag.__table__.create()
    artwork_tags.create()

    Label.__table__.create()
    artwork_labels.create()

    # Tag-related permissions
    add_tags = Privilege(name=u'add_tags', description=u'Can add tags with no restrictions')
    remove_tags = Privilege(name=u'remove_tags', description=u'Can remove tags with no restrictions')

    Session = sessionmaker(bind=migrate_engine)()
    Session.add(add_tags)
    Session.add(remove_tags)
    for role in Session.query(Role).filter(Role.name.in_([ u'user', u'admin' ])):
        Session.add(RolePrivilege(role_id=role.id, priv_id=add_tags.id))
        Session.add(RolePrivilege(role_id=role.id, priv_id=remove_tags.id))
    Session.commit()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    artwork_labels.drop()
    Label.__table__.drop()

    artwork_tags.drop()
    Tag.__table__.drop()

    # Nuke the privs
    Session = sessionmaker(bind=migrate_engine)()
    q = Session.query(Privilege).filter(
        Privilege.name.in_([ u'add_tags', u'remove_tags' ]))

    Session.query(RolePrivilege) \
        .filter(RolePrivilege.priv_id.in_(_.id for _ in q)) \
        .delete(synchronize_session=False)
    q.delete(synchronize_session=False)
    Session.commit()
