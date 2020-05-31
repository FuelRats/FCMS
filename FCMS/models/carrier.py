from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Boolean, DateTime, ForeignKey,
)

from .meta import Base


class Carrier(Base):
    __tablename__ = 'carriers'
    id = Column(Integer, primary_key=True)
    owner = Column(Integer, ForeignKey('users.id'))
    callsign = Column(Text)
    name = Column(Text)
    currentStarSystem = Column(Text)
    x = Column(Integer)
    y = Column(Integer)
    z = Column(Integer)
    balance = Column(Integer)
    fuel = Column(Integer)
    state = Column(Text)
    theme = Column(Text)
    dockingAccess = Column(Text)
    notoriousAccess = Column(Boolean)
    totalDistanceJumped = Column(Integer)
    currentJump = Column(Text)
    taxation = Column(Integer)
    coreCost = Column(Integer)
    servicesCost = Column(Integer)
    jumpsCost = Column(Integer)
    numJumps = Column(Integer)
    hasCommodities = Column(Boolean)
    hasCarrierFuel = Column(Boolean)
    hasRefuel = Column(Boolean)
    hasRepair = Column(Boolean)
    hasRearm = Column(Boolean)
    hasShipyard = Column(Boolean)
    hasOutfitting = Column(Boolean)
    hasBlackMarket = Column(Boolean)
    hasVoucherRedemption = Column(Boolean)
    hasExploration = Column(Boolean)
    lastUpdated = Column(DateTime)


Index('carrier_index', Carrier.id, unique=True)
Index('carrier_callsign_index', Carrier.callsign)
