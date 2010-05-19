from sqlalchemy import *
from migrate import *

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()


class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)

class IdentityURL(TableBase):
    __tablename__ = 'identity_urls'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    url = Column(Unicode(250), nullable=False, index=True, unique=True)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    User.__table__.create()
    IdentityURL.__table__.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    IdentityURL.__table__.drop()
    User.__table__.drop()
