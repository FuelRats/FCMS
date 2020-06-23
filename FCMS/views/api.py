import json
from datetime import datetime, timedelta

from pyramid.view import view_config

import pyramid.httpexceptions as exc
from pyramid_storage.exceptions import FileNotAllowed

from ..models import carrier, CarrierExtra, Calendar, Webhook, User, Carrier
from ..models.routes import RouteCalendar, Route

from ..utils import carrier_data
from ..utils import menu, user as usr, webhooks
from humanfriendly import format_timespan
import logging

from ..utils.carrier_data import update_carrier

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
    if not user:
        print("Bad user.")
        raise exc.HTTPBadRequest(detail='Invalid API key.')
    if pvars['key'] != user.apiKey:
        print("Bad key.")
        raise exc.HTTPBadRequest(detail='Invalid API key.')
    if pvars['cmdr'] != user.cmdr_name:
        print("CMDR name mismatch")
        raise exc.HTTPBadRequest(detail='Data not for correct CMDR.')
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
                    if mycarrier.lastUpdated:
                        if mycarrier.lastUpdated < datetime.now() - timedelta(minutes=15):
                            log.debug("Refreshing carrier data before sending webhook.")
                            update_carrier(request, mycarrier.id, request.user)
                            request.dbsession.flush()
                            request.dbsession.refresh(mycarrier)
                    print("Check for route schedules...")
                    rc = request.dbsession.query(RouteCalendar).filter(RouteCalendar.carrier_id == mycarrier.id)
                    if rc:
                        print(f"Have RC. {rc}")
                        for row in rc:
                            print(f"Process Calendar {row}")
                            if row.isActive:
                                print(f"Active route calendar.")
                                route = request.dbsession.query(Route).filter(Route.id == row.route_id).one_or_none()
                                waypoints = json.loads(route.waypoints)
                                for wp in waypoints:
                                    print(wp)
                                    if wp['system'] == data['SystemName']:
                                        print("System is on route!")
                                        row.currentWaypoint = data['SystemName']
                                        request.dbsession.flush()
                                        request.dbsession.refresh(row)
                                        # Jump is to a route waypoint, fire route jumps instead and update CWP.
                                        if hook['webhook_type'] == 'discord' and hook['jumpEvents']:
                                            res = webhooks.announce_route_jump(request, mycarrier.id, row.id,
                                                                               hook['webhook_url'])
                                            log.debug(f"Route jump result: {res}")

                    else:
                        if hook['webhook_type'] == 'discord' and hook['jumpEvents']:
                            if 'Body' in data:
                                res = webhooks.announce_jump(request, mycarrier.id, data['SystemName'],
                                                             hook['webhook_url'], body=data['Body'])
                            else:
                                res = webhooks.announce_jump(request, mycarrier.id, data['SystemName'],
                                                             hook['webhook_url'])
                            log.debug(f"Hook result: {res}")

        elif data['event'] == 'CarrierJumpCancelled':
            print("Jump cancelled!")
            hooks = webhooks.get_webhooks(request, mycarrier.id)
            if hooks:
                print("Have hook, will fire.")
                for hook in hooks:
                    log.debug(f"Process hook {hook['webhook_url']}")
                    if hook['webhook_type'] == 'discord' and hook['jumpEvents']:
                        res = webhooks.cancel_jump(request, mycarrier.id, hook['webhook_url'], False)
                        log.debug(f"Hook result: {res}")
        elif data['event'] == 'MarketUpdate':
            hooks = webhooks.get_webhooks(request, mycarrier.id)
            if hooks:
                print("Have hook, will fire.")
                for hook in hooks:
                    log.debug(f"Process hook {hook['webhook_url']}")
                    if hook['webhook_type'] == 'discord' and hook['marketEvents']:
                        res = webhooks.market_update(request, mycarrier.id, None, hook['webhook_url'])
                        log.debug(f"Hook result: {res}")

    return {'Status': 'Maybe OK?'}
