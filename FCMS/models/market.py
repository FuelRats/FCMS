from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime, ForeignKey,
)

from .meta import Base


class Market(Base):
    __tablename__ = 'market'
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer, ForeignKey('carriers.id'))
    commodity_id = Column(Integer)
    categoryname = Column(Text)
    name = Column(Text)
    locName = Column(Text)
    stock = Column(Integer)
    buyPrice = Column(Integer)
    sellPrice = Column(Integer)
    demand = Column(Integer)


Index('market_index', Market.id, unique=True)
Index('market_cid_index', Market.carrier_id)
