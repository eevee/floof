from sqlalchemy import *
from migrate import *
import migrate.changeset  # monkeypatches Column

from floof.model import now
from floof.model.types import TZDateTime

from sqlalchemy.ext.declarative import declarative_base
TableBase = declarative_base()

# Modified tables
class Artwork(TableBase):
    __tablename__ = 'artwork'
    id = Column(Integer, primary_key=True, nullable=False)
    resource_id = Column(Integer, nullable=False)
    media_type = Column(Enum(u'image', u'text', u'audio', u'video', name='artwork_media_type'), nullable=False)
    title = Column(Unicode(133), nullable=False)
    hash = Column(Unicode(256), nullable=False, unique=True, index=True)
    uploader_user_id = Column(Integer, nullable=False)
    uploaded_time = Column(TZDateTime, nullable=False, index=True, default=now)
    created_time = Column(TZDateTime, nullable=False, index=True, default=now)
    original_filename = Column(Unicode(255), nullable=False)
    mime_type = Column(Unicode(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    rating_count = Column(Integer, nullable=False, default=0)
    rating_sum = Column(Float, nullable=False, default=0)
    rating_score = Column(Float, nullable=True, default=None)
    remark = Column(UnicodeText, nullable=False, server_default=u'')


def upgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Artwork.__table__.c.remark.create()

def downgrade(migrate_engine):
    TableBase.metadata.bind = migrate_engine
    Artwork.__table__.c.remark.drop()
