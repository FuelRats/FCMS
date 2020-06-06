from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime,
)

from .meta import Base


class Cargo(Base):
    __tablename__ = 'cargo'
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer)
    commodity = Column(Text)
    locName = Column(Text)
    quantity = Column(Integer)
    stolen = Column(Boolean)
    value = Column(Integer)


Index('cargo_index', Cargo.id, unique=True)
Index('cargo_cid_index', Cargo.carrier_id)
