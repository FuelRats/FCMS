from datetime import datetime, timedelta

from pyramid.view import view_config

import pyramid.httpexceptions as exc
from pyramid_storage.exceptions import FileNotAllowed

from ..models import carrier, CarrierExtra, Calendar, Webhook, User, Carrier

from ..utils import carrier_data
from ..utils import menu, user as usr, webhooks
from humanfriendly import format_timespan
import logging

log = logging.getLogger(__name__)


@view_config(route_name='api', renderer='json')
def api_view(request):
    print(f"Post: {request.json}")
    pvars = request.json
    if not pvars:
        print("No Pvars")
        raise exc.HTTPBadRequest(detail='Invalid API request.')
    if 'user' not in pvars or 'key' not in pvars:
        print("No user")
        raise exc.HTTPBadRequest(detail='Invalid API request.')
    user = request.dbsession.query(User).filter(User.username == pvars['user']).one_or_none()
    if pvars['key'] != user.apiKey:
        print("Bad key.")
        raise exc.HTTPBadRequest(detail='Invalid API key.')
    else:
        data = pvars['data']
        print(f"Got valid data post: {data}")
        mycarrier = request.dbsession.query(Carrier).filter(Carrier.owner == user.id).one_or_none()
        if data['event'] == 'CarrierJumpRequest':
            print("Jump request!")
            hooks = webhooks.get_webhooks(request, mycarrier.id)
            if hooks:
                print("Have hook, will fire.")
                for hook in hooks:
                    log.debug(f"Process hook {hook['webhook_url']}")
                    if hook['webhook_type'] == 'discord':
                        res = webhooks.announce_jump(request, mycarrier.id, data['SystemName'],
                                                     hook['webhook_url'], body=data['Body'])
                        log.debug(f"Hook result: {res}")

        elif data['event'] == 'CarrierJumpCancelled':
            print("Jump cancelled!")
            hooks = webhooks.get_webhooks(request, mycarrier.id)
            if hooks:
                print("Have hook, will fire.")
                for hook in hooks:
                    log.debug(f"Process hook {hook['webhook_url']}")
                    if hook['webhook_type'] == 'discord':
                        res = webhooks.cancel_jump(request, mycarrier.id, hook['webhook_url'])
                        log.debug(f"Hook result: {res}")

    return {'Status': 'Maybe OK?'}
