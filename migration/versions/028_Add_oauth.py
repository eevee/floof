from sqlalchemy import *
from migrate import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from floof.model.types import TZDateTime
TableBase = declarative_base()


# Stub tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)


# New tables
OAUTH2_CLIENT_IDENTIFIER_LEN = 32
OAUTH2_CLIENT_SECRET_LEN = 64

class OAuth2Client(TableBase):
    __tablename__ = 'oauth2_clients'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    identifier = Column(String(OAUTH2_CLIENT_IDENTIFIER_LEN), nullable=False, unique=True, index=True)
    type = Column(Enum(
        u'web',
        u'native',
        name='oauth2_client_type'), nullable=False, index=True)
    name = Column(Unicode(127), nullable=False)
    site_uri = Column(Unicode)
    created = Column(TZDateTime, nullable=False)
    updated = Column(TZDateTime, nullable=False)
    __mapper_args__ = {'polymorphic_on': type}

class OAuth2WebClient(OAuth2Client):
    __mapper_args__ = {'polymorphic_identity': u'web'}
    secret = Column(String(OAUTH2_CLIENT_SECRET_LEN), nullable=False)

class OAuth2NativeClient(OAuth2Client):
    __mapper_args__ = {'polymorphic_identity': u'native'}

class OAuth2RedirectURI(TableBase):
    __tablename__ = 'oauth2_redirect_uris'
    id = Column(Integer, primary_key=True)
    position = Column(Integer)
    client_id = Column(Integer, ForeignKey('oauth2_clients.id'), nullable=False, index=True)
    uri = Column(Unicode, nullable=False)

class OAuth2Grant(TableBase):
    __tablename__ = 'oauth2_grants'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('oauth2_clients.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    redirect_uri = Column(Unicode, nullable=False)
    redirect_uri_supplied = Column(Boolean, nullable=False)
    code = Column(String(128), nullable=False, unique=True, index=True)
    created = Column(TZDateTime, nullable=False)
    expires = Column(TZDateTime, nullable=False, index=True)
    refresh_token_id = Column(Integer, ForeignKey('oauth2_refresh_tokens.id'))

class OAuth2RefreshToken(TableBase):
    __tablename__ = 'oauth2_refresh_tokens'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('oauth2_clients.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(Unicode(128), nullable=False, unique=True, index=True)
    created = Column(TZDateTime, nullable=False)

class OAuth2AccessToken(TableBase):
    __tablename__ = 'oauth2_access_tokens'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('oauth2_clients.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(Unicode(128), nullable=False, unique=True, index=True)
    refresh_token_id = Column(Integer, ForeignKey('oauth2_refresh_tokens.id'))
    created = Column(TZDateTime, nullable=False)
    expires = Column(TZDateTime, nullable=False, index=True)

class Scope(TableBase):
    __tablename__ = 'scopes'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode)

oauth2_grant_scopes = Table('oauth2_grant_scopes', TableBase.metadata,
    Column('token_id', Integer, ForeignKey('oauth2_grants.id'), primary_key=True),
    Column('scope_id', Integer, ForeignKey('scopes.id'), primary_key=True),
)

oauth2_refresh_token_scopes = Table('oauth2_refresh_token_scopes', TableBase.metadata,
    Column('token_id', Integer, ForeignKey('oauth2_refresh_tokens.id'), primary_key=True),
    Column('scope_id', Integer, ForeignKey('scopes.id'), primary_key=True),
)

oauth2_access_token_scopes = Table('oauth2_access_token_scopes', TableBase.metadata,
    Column('token_id', Integer, ForeignKey('oauth2_access_tokens.id'), primary_key=True),
    Column('scope_id', Integer, ForeignKey('scopes.id'), primary_key=True),
)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    OAuth2Client.__table__.create()
    OAuth2RedirectURI.__table__.create()
    OAuth2RefreshToken.__table__.create()
    OAuth2Grant.__table__.create()
    OAuth2AccessToken.__table__.create()
    Scope.__table__.create()
    oauth2_grant_scopes.create()
    oauth2_refresh_token_scopes.create()
    oauth2_access_token_scopes.create()

    # Default scopes
    scopes = (
        (u'art', u'Upload and edit artworks'),
        (u'comment', u'Post and edit comments'),
        (u'rate', u'Rate artworks'),
    )

    session = sessionmaker(bind=migrate_engine)()
    for name, desc in scopes:
        scope = Scope(name=name, description=desc)
        session.add(scope)
    session.commit()


def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    oauth_type = OAuth2Client.__table__.c.type.type
    oauth2_access_token_scopes.drop()
    oauth2_refresh_token_scopes.drop()
    oauth2_grant_scopes.drop()
    Scope.__table__.drop()
    OAuth2AccessToken.__table__.drop()
    OAuth2Grant.__table__.drop()
    OAuth2RefreshToken.__table__.drop()
    OAuth2RedirectURI.__table__.drop()
    OAuth2Client.__table__.drop()
    oauth_type.drop(migrate_engine)
