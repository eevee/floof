import datetime

from sqlalchemy import *
from sqlalchemy import sql
from migrate import *
import migrate.changeset  # monkeypatches Column

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()


# Old tables
class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)

class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)

# New tables
class Discussion(TableBase):
    __tablename__ = 'discussions'
    id = Column(Integer, primary_key=True, nullable=False)
    comment_count = Column(Integer, nullable=False, default=0)

class Comment(TableBase):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)
    posted_time = Column(DateTime, nullable=False, index=True, default=datetime.datetime.now)
    author_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    left = Column(Integer, index=True, nullable=False)
    right = Column(Integer, index=True, nullable=False)
    content = Column(UnicodeText(4096), nullable=False)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    Discussion.__table__.create()
    Comment.__table__.create()

    Artwork.__table__.c.discussion_id.nullable = True
    Artwork.__table__.c.discussion_id.create()
    User.__table__.c.discussion_id.nullable = True
    User.__table__.c.discussion_id.create()

    # Create a new discussion for each artwork and user
    conn = migrate_engine.connect()
    tr = conn.begin()

    for table in Artwork, User:
        for id, in conn.execute( sql.select([table.id]) ):
            res = conn.execute( sql.insert(Discussion.__table__) )
            discussion_id = res.inserted_primary_key[0]

            conn.execute(sql.update(
                table.__table__,
                table.__table__.c.id == id,
                dict(discussion_id=discussion_id),
            ))

    tr.commit()

    Artwork.__table__.c.discussion_id.alter(nullable=False)
    User.__table__.c.discussion_id.alter(nullable=False)


def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    Artwork.__table__.c.discussion_id.drop()
    User.__table__.c.discussion_id.drop()
    Comment.__table__.drop()
    Discussion.__table__.drop()
