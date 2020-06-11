from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime, ForeignKey,
)

from .meta import Base


class Webhook(Base):
    __tablename__ = 'webhooks'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    carrier_id = Column(Integer, ForeignKey('carriers.id'))
    hook_url = Column(Text)
    hook_type = Column(Text)
    enabled = Column(Boolean)


Index('webhooks_index', Webhook.id, unique=True)
Index('webhooks_cid_index', Webhook.carrier_id)
Index('webhooks_owner_index', Webhook.owner_id)
