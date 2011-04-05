from sqlalchemy import *
from migrate import *

from sqlalchemy.ext.declarative import declarative_base

from floof.model.types import Timezone

TableBase = declarative_base()

# Modified tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)
    display_name = Column(Unicode(24), nullable=True)
    has_trivial_display_name = Column(Boolean, nullable=False, default=False)
    timezone = Column(Timezone, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    auth_method = Column(Enum(
        u'cert_only',
        u'openid_only',
        u'cert_or_openid',
        u'cert_and_openid',
        name='user_auth_method'), nullable=False, default=u'openid_only')


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    User.__table__.c.display_name.create()
    User.__table__.c.has_trivial_display_name.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    User.__table__.c.display_name.drop()
    User.__table__.c.has_trivial_display_name.drop()
