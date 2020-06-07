from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime,
)

from .meta import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(Text)
    password = Column(Text)
    userlevel = Column(Integer)
    carrierid = Column(Integer)
    cmdr_name = Column(Text)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expiration = Column(Integer)
    has_validated = Column(Boolean)
    public_carrier = Column(Boolean)
    banned = Column(Boolean)
    cachedJson = Column(Text)
    lastUpdated = Column(DateTime)


Index('user_index', User.username, unique=True)
