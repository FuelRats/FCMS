from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Boolean,
)

from .meta import Base


class Carrier(Base):
    __tablename__ = 'carriers'
    id = Column(Integer, primary_key=True)
    callsign = Column(Text)
    name = Column(Text)
    currentStarSystem = Column(Integer)
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


Index('carrier_index', Carrier.id, unique=True)
