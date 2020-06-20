from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text, Boolean, DateTime, ForeignKey,
)
import colander
from .meta import Base


class Webhook(Base):
    __tablename__ = 'webhooks'
    id = Column(Integer, primary_key=True,
                info={'colanderalchemy': {
                    'typ': colander.Integer(),
                }})
    owner_id = Column(Integer, ForeignKey('users.id'),
                      info={'colanderalchemy': {
                          'typ': colander.Integer(),
                      }})
    carrier_id = Column(Integer, ForeignKey('carriers.id'),
                        info={'colanderalchemy': {
                            'typ': colander.Integer(),

                        }})
    hook_url = Column(Text, info={'colanderalchemy': {
        'typ': colander.String(),
        'title': 'Webhook URL'
    }})
    hook_type = Column(Text, info={'colanderalchemy': {
        'typ': colander.String(),
        'title': 'Webhook type'
    }})
    enabled = Column(Boolean, default=True, info={'colanderalchemy': {
        'typ': colander.Boolean(),
        'title': 'Boolean'
    }})
    jumpEvents = Column(Boolean, default=True)
    marketEvents = Column(Boolean, default=True)
    calendarEvents = Column(Boolean, default=True)
    isGlobal = Column(Boolean, default=False)
    description = Column(Text)


Index('webhooks_index', Webhook.id, unique=True)
Index('webhooks_cid_index', Webhook.carrier_id)
Index('webhooks_owner_index', Webhook.owner_id)
