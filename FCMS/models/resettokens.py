from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    DateTime,
    ForeignKey,
)

from .meta import Base


class ResetToken(Base):
    __tablename__ = 'reset_tokens'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    token = Column(Text, unique=True)
    expires_at = Column(DateTime)
    generated_by = Column(Text)


Index('reset_tokens_index', ResetToken.id)
