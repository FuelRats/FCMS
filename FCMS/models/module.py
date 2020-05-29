from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime,
)

from .meta import Base


class Module(Base):
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True)
    category = Column(Text)
    carrier_id = Column(Integer)
    module_id = Column(Integer)
    name = Column(Text)
    cost = Column(Integer)
    stock = Column(Integer)


Index('module_index', Module.id, unique=True)
Index('module_cid_index', Module.carrier_id)
