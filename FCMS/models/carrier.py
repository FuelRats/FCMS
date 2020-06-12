from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Binary,
    Boolean,
    DateTime,
    ForeignKey, Float, BigInteger,
)

from .meta import Base


class CarrierExtra(Base):
    __tablename__ = 'carrier_extras'
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, ForeignKey('carriers.id'))
    carrier_image = Column(Text)
    carrier_motd = Column(Text)


Index('carrier_extra_index', CarrierExtra.id)
Index('carrier_extra_cid_index', CarrierExtra.cid)


class Carrier(Base):
    __tablename__ = 'carriers'
    id = Column(Integer, primary_key=True)
    owner = Column(Integer, ForeignKey('users.id'))
    callsign = Column(Text, unique=True)
    name = Column(Text)
    currentStarSystem = Column(Text)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    balance = Column(BigInteger)
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
    capacity = Column(Integer)
    showItinerary = Column(Boolean, default=True)
    showMarket = Column(Boolean, default=True)
    showSearch = Column(Boolean, default=True)
    isDSSA = Column(Boolean)
    trackedOnly = Column(Boolean)
    lastUpdated = Column(DateTime)
    cachedJson = Column(Text)


Index('carrier_index', Carrier.id, unique=True)
Index('carrier_callsign_index', Carrier.callsign)
