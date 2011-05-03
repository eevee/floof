from sqlalchemy import *
from migrate import *
from floof.model.types import Timezone

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Modified tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)
    email = Column(Unicode(255))
    display_name = Column(Unicode(24), nullable=True)
    has_trivial_display_name = Column(Boolean, nullable=False, default=False, server_default=u'f')
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
    User.__table__.c.email.create()
###    # XXX: I think I'm missing something here, because I seem to need this
###    # .alter() to get the column creation to stick.  Eh?
###    User.__table__.c.email.alter()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    User.__table__.c.email.drop()
