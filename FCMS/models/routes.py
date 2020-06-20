from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime, ForeignKey,
)
import colander
from .meta import Base


class Route(Base):
    __tablename__ = 'routes'
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer, ForeignKey('carrier.id'))
    startPoint = Column(Text)
    endPoint = Column(Text)
    waypoints = Column(Text)
    description = Column(Text)
    start_region = Column(Integer, ForeignKey('regions.id'))
    end_region = Column(Integer, ForeignKey('regions.id'))


class Region(Base):
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    isPOI = Column(Boolean)
