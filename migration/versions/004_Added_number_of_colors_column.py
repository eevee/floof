from sqlalchemy import *
from migrate import *
import migrate.changeset  # monkeypatches Column

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

class MediaImage(TableBase):
    __tablename__ = 'media_images'
    id = Column(Integer, primary_key=True, nullable=False)
    number_of_colors = Column(Integer, nullable=False, server_default=u'16777216')  # 24-bit color


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    # Create with a useful server default so it'll be populated, then remove
    # the default
    MediaImage.__table__.c.number_of_colors.create()
    MediaImage.__table__.c.number_of_colors.alter(server_default=None)

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine

    MediaImage.__table__.c.number_of_colors.drop()
