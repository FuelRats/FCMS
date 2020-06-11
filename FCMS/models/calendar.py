from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Boolean, DateTime, ForeignKey,
)

from .meta import Base


class Calendar(Base):
    __tablename__ = 'calendar'
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer, ForeignKey('carriers.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    title = Column(Text)
    start = Column(DateTime)
    end = Column(DateTime)
    bgcolor = Column(Text)
    fgcolor = Column(Text)
    url = Column(Text)
    allday = Column(Boolean)
    is_global = Column(Boolean)
    departureSystem = Column(Text)
    arrivalSystem = Column(Text)


Index('calendar_index', Calendar.id, unique=True)
Index('calendar_cid_index', Calendar.carrier_id)
