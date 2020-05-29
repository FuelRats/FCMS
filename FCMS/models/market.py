from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime,
)

from .meta import Base


class Market(Base):
    __tablename__ = 'market'
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer)
    commodity_id = Column(Integer)
    categoryname = Column(Text)
    name = Column(Text)
    locName = Column(Text)
    stock = Column(Integer)
    buyPrice = Column(Integer)
    sellPrice = Column(Integer)
    demand = Column(Integer)
