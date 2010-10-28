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

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    User.__table__.c.timezone.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    User.__table__.c.timezone.drop()
