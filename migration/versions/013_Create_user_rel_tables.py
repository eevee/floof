from sqlalchemy import *
from migrate import *

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint
TableBase = declarative_base()

# Old table stubs
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)


# New tables
user_relationship_types = (u'watch.art', u'watch.journals', u'friend', u'ignore')
class UserRelationship(TableBase):
    __tablename__ = 'user_relationships'
    __table_args__ = (
        UniqueConstraint('user_id', 'other_user_id', 'relationship_type'),
        {},
    )

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    other_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    relationship_type = Column(Enum(*user_relationship_types, name='user_relationships_relationship_type'), nullable=False)
    created_time = Column(DateTime, nullable=False, index=True)

def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    UserRelationship.__table__.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    UserRelationship.__table__.drop()
