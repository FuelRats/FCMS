from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
)

from .meta import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(Text)
    password = Column(Text)
    userlevel = Column(Integer)
    carrierid = Column(Integer)


Index('user_index', User.username, unique=True)
