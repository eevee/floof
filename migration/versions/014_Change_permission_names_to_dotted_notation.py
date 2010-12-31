from sqlalchemy import *
from migrate import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Stub
class Privilege(TableBase):
    __tablename__ = 'privileges'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode(127), nullable=False)
    description = Column(Unicode, nullable=True)

privmaps = [dict(old=old, new=new) for old, new in [
        (u'admin',           u'admin.view'),
        (u'upload_art',      u'art.upload'),
        (u'write_comment',   u'comments.add'),
        (u'add_tags',        u'tags.add'),
        (u'remove_tags',     u'tags.remove'),
        ]]

def upgrade(migrate_engine):
    Session = sessionmaker(bind=migrate_engine)()
    for privmap in privmaps:
        priv = Session.query(Privilege).filter(Privilege.name==privmap['old']).first()
        priv.name = privmap['new']
    Session.commit()

def downgrade(migrate_engine):
    Session = sessionmaker(bind=migrate_engine)()
    for privmap in privmaps:
        priv = Session.query(Privilege).filter(Privilege.name==privmap['new']).first()
        priv.name = privmap['old']
    Session.commit()
