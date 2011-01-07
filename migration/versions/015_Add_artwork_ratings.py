from sqlalchemy import *
from migrate import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, class_mapper, relation, validates
TableBase = declarative_base()

from migrate.changeset import schema
meta = MetaData()
artwork_ratings = Table('artwork_ratings', meta,
  Column('rating', Integer(),  nullable=False),
  Column('artwork_id', Integer(),  primary_key=True, nullable=False),
  Column('user_id', Integer(),  primary_key=True, nullable=False),
)
user_artwork = Table('user_artwork', meta,
  Column('user_id', Integer(),  primary_key=True, nullable=False),
  Column('artwork_id', Integer(),  primary_key=True, nullable=False),
  Column('relationship_type', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  primary_key=True, nullable=False),
)
users = Table('users', meta,
  Column('id', Integer(),  primary_key=True, nullable=False),
  Column('resource_id', Integer(),  nullable=False),
  Column('name', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  nullable=False),
  Column('timezone', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False)),
  Column('role_id', Integer(),  nullable=False),
)
artwork = Table('artwork', meta,
  Column('id', Integer(),  primary_key=True, nullable=False),
  Column('resource_id', Integer(),  nullable=False),
  Column('media_type', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  nullable=False),
  Column('title', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  nullable=False),
  Column('hash', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  nullable=False),
  Column('uploader_user_id', Integer(),  nullable=False),
  Column('uploaded_time', DateTime(timezone=False),  nullable=False),
  Column('created_time', DateTime(timezone=False),  nullable=False),
  Column('original_filename', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  nullable=False),
  Column('mime_type', String(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False),  nullable=False),
  Column('file_size', Integer(),  nullable=False),
  Column('rating_sum', Integer(), nullable=False, default=0, server_default="0"),
  Column('num_ratings', Integer(), nullable=False, default=0, server_default="0"),
)
class Privilege(TableBase):
    __tablename__ = 'privileges'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

class Role(TableBase):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

class RolePrivilege(TableBase):
    __tablename__ = 'role_privileges'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, nullable=False)
    priv_id = Column(Integer, ForeignKey('privileges.id'), primary_key=True, nullable=False)

Role.privileges = relation(Privilege, secondary=RolePrivilege.__table__)

priv = (u'art.rate',           u'Can rate art')

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    artwork_ratings.drop()
    artwork.columns['rating_sum'].drop()
    artwork.columns['num_ratings'].drop()

    Session = sessionmaker(bind=migrate_engine)()
    to_remove = Session.query(Privilege).filter_by(name=priv[0]).one()
    user = Session.query(Role).filter_by(name=u'user').one()
    user.privileges.remove(to_remove)
    Session.delete(to_remove)
    Session.commit()

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    meta.bind = migrate_engine
    artwork_ratings.create()
    artwork.columns['rating_sum'].create(table=artwork)
    artwork.columns['num_ratings'].create(table=artwork)

    Session = sessionmaker(bind=migrate_engine)()
    to_add = Privilege(name=priv[0], description=priv[0])
    Session.add(to_add)
    user = Session.query(Role).filter_by(name=u'user').one()
    user.privileges.append(to_add)
    Session.commit()
