"""The application's model objects"""
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation
from sqlalchemy.types import *

from floof.model import meta

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    meta.Session.configure(bind=engine)
    meta.engine = engine


TableBase = declarative_base()

### USERS

class AnonymousUser(object):
    """Fake not-logged-in user.

    Tests as false and generally responds correctly to User methods.
    """

    def __nonzero__(self):
        return False
    def __bool__(self):
        return False

class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(24), nullable=False, index=True, unique=True)

    @property
    def display_name(self):
        """Returns a flavory string that should be used to present this user.
        """

        return self.name

class IdentityURL(TableBase):
    __tablename__ = 'identity_urls'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    url = Column(Unicode(250), nullable=False, index=True, unique=True)



### RELATIONS

# Users
IdentityURL.user = relation(User, backref='identity_urls')
