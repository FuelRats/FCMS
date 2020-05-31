from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime, ForeignKey,
)

from .meta import Base


class Ship(Base):
    __tablename__ = 'ships'
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer, ForeignKey('carriers.id'))
    ship_id = Column(Integer)
    name = Column(Text)
    basevalue = Column(Integer)
    stock = Column(Integer)


Index('ship_index', Ship.id, unique=True)
Index('ship_cid_index', Ship.carrier_id)
