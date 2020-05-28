from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean,
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
    has_validated = Column(Boolean)
    public_carrier = Column(Boolean)
    banned = Column(Boolean)


Index('user_index', User.username, unique=True)
