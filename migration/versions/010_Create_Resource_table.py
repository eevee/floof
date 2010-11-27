from sqlalchemy import *
from migrate import *
import migrate.changeset  # monkeypatches Column

from sqlalchemy.schema import DefaultClause
from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Gonna swap out discussion_id for resource_id...

class Resource(TableBase):
    __tablename__ = 'resources'
    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(Enum(u'artwork', u'users', name='resources_type'), nullable=False)


class User(TableBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)

class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    discussion_id = Column(Integer, ForeignKey('discussions.id'), nullable=False)

class Discussion(TableBase):
    __tablename__ = 'discussions'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=False)
    comment_count = Column(Integer, nullable=False)


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    Resource.__table__.create()

    resource_column = Discussion.__table__.c.resource_id
    resource_column.nullable = True
    resource_column.create()

    for table in (User, Artwork):
        table.__table__.c.resource_id.nullable = True
        table.__table__.c.resource_id.create()

        conn = migrate_engine.connect()
        tr = conn.begin()
        for id, discussion_id in conn.execute(
            select([table.id, table.discussion_id])):

            res = conn.execute(
                insert(Resource.__table__, {'type': table.__tablename__})
            )
            resource_id = res.inserted_primary_key[0]

            conn.execute(
                update(Discussion.__table__,
                    Discussion.id == discussion_id,
                    { 'resource_id': resource_id },
                )
            )
            conn.execute(
                update(table.__table__,
                    table.id == id,
                    { 'resource_id': resource_id },
                )
            )
        tr.commit()
        conn.close()

        table.__table__.c.resource_id.alter(nullable=False)
        table.__table__.c.discussion_id.drop()

    resource_column.alter(nullable=False)

def downgrade(migrate_engine):
    # I cannot be bothered right now.
    raise NotImplementedError
