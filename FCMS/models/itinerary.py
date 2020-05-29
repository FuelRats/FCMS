from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime,
)

from .meta import Base


class Itinerary(Base):
    __tablename__ = 'itinerary'
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer)
    starsystem = Column(Text)
    departureTime = Column(DateTime)
    arrivalTime = Column(DateTime)
    visitDurationSeconds = Column(Integer)


Index('itinerary_index', Itinerary.id, unique=True)
Index('itinerary_cid_index', Itinerary.carrier_id)
