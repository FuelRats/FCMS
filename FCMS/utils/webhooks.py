# Webhooks for carrier events. Can fire from EDDN hits or calendar create/delete events.

from datetime import datetime, timedelta
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from humanfriendly import format_number
from sqlalchemy import or_

from ..models import Carrier, Calendar, CarrierExtra, Webhook, Market, User, Route, Region
from ..utils import util
import json
import logging

log = logging.getLogger(__name__)


def send_webhook(hookurl, message=None, hooktype='generic', myembed=None):
    """
    Executes a webhook. Tries to send event to the specified hook URL.
    :param hooktype: Type of webhook (Discord webhook, generic event)
    :param myembed: If Discord, the embed to send to the webhook
    :param hookurl: The URL to send the webhook to
    :param message: JSON body to send
    :return: True if webhook is successfully delivered, else False
    """
    if hooktype == 'discord':
        webhook = DiscordWebhook(url=hookurl)
        if myembed:
            webhook.add_embed(myembed)
            return webhook.execute()
        return webhook.execute()
    else:
        r = requests.post(url=hookurl, data=message)
        return r


def populate_webhook(request, user):
    """
    Populates user and carrier datafields for a webhook request
    :param request: The request object
    :param user: The user being serialized for the request.
    :return: A dict of data
    """
    user = request.dbsession.query(User).filter(User.id == 1).one_or_none()
    carrier = request.dbsession.query(Carrier).filter(Carrier.owner == 1).one_or_none()
    if user:
        return dict({'cmdr_name': user.cmdr_name, 'carrier_callsign': carrier.callsign, 'carrier_vanity_name':
            carrier.name, 'docking_access': carrier.dockingAccess, 'current_starsystem': carrier.currentStarSystem,
                     'notorious_access': carrier.notoriousAccess, 'taxation': carrier.taxation,
                     'has_refuel': carrier.hasRefuel, 'has_repair': carrier.hasRepair, 'has_rearm': carrier.hasRearm})


def calendar_generic(request, calendar_id, webhook_url):
    """
    Executes a generic calendar webhook
    :param request: The request object
    :param calendar_id: Calendar ID of event to send
    :param webhook_url: The webhook URL
    :return: Request status object
    """

    calendar = request.dbsession.query(Calendar).filter(Calendar.id == calendar_id).one_or_none()
    if calendar:
        generic = populate_webhook(request, Calendar.owner_id)
        data = {'calendar_title': calendar.title, 'calendar_start': str(calendar.start),
                'calendar_end': str(calendar.end),
                'calendar_url': calendar.url, 'calendar_allday': calendar.allday,
                'calendar_departureSystem': calendar.departureSystem,
                'calendar_arrivalSystem': calendar.arrivalSystem}
        indata = {**generic, **data}
        myjson = json.dumps(indata)
        log.debug(str(indata))
        # send_webhook(webhook_url, myjson, hooktype='generic')
    return myjson


def schedule_jump(request, calendar_id, webhook_url):
    """
    Fires a webhook for a jump calendar event.
    :param webhook_url: The webhook URL
    :param request: The request object
    :param calendar_id: Calendar ID for event
    :return: Result of webhook firing
    """
    cdata = request.dbsession.query(Calendar).filter(Calendar.id == calendar_id).one_or_none()
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cdata.carrier_id).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cdata.carrier_id).one_or_none()
    if not cdata:
        return None
    embed = DiscordEmbed(title='Scheduled Jump',
                         description=f'{mycarrier.callsign} {util.from_hex(mycarrier.name)} has scheduled a jump.',
                         color=242424,
                         url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    embed.set_author(name='Fleetcarrier.space', url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    if extra:
        embed.set_image(url=request.storage.url(extra.carrier_image))
    else:
        embed.set_image(url='https://fleetcarrier.space/static/img/carrier_default.png')
    embed.set_footer(text='Fleetcarrier.space - Fleet Carrier Management System')
    embed.add_embed_field(name='Departing from', value=cdata.departureSystem)
    embed.add_embed_field(name='Headed to', value=cdata.arrivalSystem)
    embed.add_embed_field(name='Departure time', value=str(cdata.start))
    embed.set_timestamp()
    return send_webhook(webhook_url, 'Carrier Jump scheduled', hooktype='discord', myembed=embed)


def generic_market_update(request, cid, items, webhook_url, message=None):
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cid).one_or_none()
    market = request.dbsession.query(Market).filter(Market.carrier_id == cid).all()
    data = {}

    for item in market:

        if item.categoryname == 'NonMarketable':
            continue
        if items and str(item.id) not in items:
            continue

        if item.stock > 0:
            ldata = {'Selling': item.name, 'For': item.buyPrice, 'Quantity': item.stock}
            data[item.name] = ldata
        if item.demand > 0:
            ldata = {'Buying': item.name, 'For': item.sellPrice, 'Quantity': item.deman}
            data[item.name] = ldata
    data['Current Location'] = mycarrier.currentStarSystem
    data['Docking Access'] = mycarrier.dockingAccess
    if message:
        data['Message'] = message
    return send_webhook(webhook_url, data, hooktype='generic')


def market_update(request, cid, items, webhook_url, message=None):
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cid).one_or_none()
    embed = DiscordEmbed(title='Priority Market Update',
                         description=f'{mycarrier.callsign} {util.from_hex(mycarrier.name)} has issued a market '
                                     f'notification.', color=242424,
                         url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    embed.set_author(name='Fleetcarrier.space', url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    if extra:
        embed.set_image(url=request.storage.url(extra.carrier_image))
    else:
        embed.set_image(url='https://fleetcarrier.space/static/img/carrier_default.png')
    embed.set_footer(text='Fleetcarrier.space - Fleet Carrier Management System')

    market = request.dbsession.query(Market).filter(Market.carrier_id == cid).all()
    for item in market:

        if item.categoryname == 'NonMarketable':
            continue
        if items and str(item.id) not in items:
            continue
        if item.stock > 0:
            embed.add_embed_field(name='Selling', value=item.name)
            embed.add_embed_field(name='For', value=format_number(item.buyPrice))
            embed.add_embed_field(name='Quantity', value=format_number(item.stock))
        if item.demand > 0:
            embed.add_embed_field(name='Buying', value=item.name)
            embed.add_embed_field(name='For', value=format_number(item.sellPrice))
            embed.add_embed_field(name='Quantity', value=format_number(item.demand))
    embed.add_embed_field(name='Current Location', value=mycarrier.currentStarSystem)
    embed.add_embed_field(name='Docking Access',
                          value='Squadron and Friends' if mycarrier.dockingAccess == 'squadronfriends' else mycarrier.dockingAccess.title())
    embed.set_timestamp()
    if message:
        embed.add_embed_field(name='Message', value=message, inline=False)
    return send_webhook(webhook_url, 'Priority Market Update', hooktype='discord', myembed=embed)


def announce_route_scheduled(request, cid, routeid, webhook_url):
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cid).one_or_none()
    route = request.dbsession.query(Route).filter(Route.id == routeid).one_or_none()
    embed = DiscordEmbed(title='Route Departure Scheduled',
                         description=f'{mycarrier.callsign} {util.from_hex(mycarrier.name)} is traveling a planned route.',
                         color=242424,
                         url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}/route/')
    embed.set_author(name='Fleetcarrier.space', url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    if extra:
        embed.set_image(url=request.storage.url(extra.carrier_image))
    else:
        embed.set_image(url='https://fleetcarrier.space/static/img/carrier_default.png')
    sr = request.dbsession.query(Region).filter(Region.id == route.start_region).one_or_none()
    er = request.dbsession.query(Region).filter(Region.id == route.end_region).one_or_none()
    tod = datetime.now()

    embed.add_embed_field(name='Departing from', value=sr.name)
    embed.add_embed_field(name='Headed to', value=er.name)
    embed.add_embed_field(name='Starting from', value=route.startPoint)
    wpcount = 1
    tod = datetime.now()
    for wp in json.loads(route.waypoints):
        embed.add_embed_field(name=f'Waypoint {wpcount}', value=wp['system'], inline=True)
        embed.add_embed_field(name=f'Layover', value=wp['duration'], inline=True)
        ter = datetime.strptime(wp['duration'], "%H:%M:%S")
        eta = tod + timedelta(hours=ter.hour, minutes=ter.minute, seconds=ter.second)
        embed.add_embed_field(name='ETA', value=f'{str(eta)}')
        tod = eta
        wpcount = wpcount+1
    embed.add_embed_field(name='Final Destination', value=route.endPoint)
    embed.add_embed_field(name='Departure Time', value=str(datetime.now()))
    embed.set_footer(text='Fleetcarrier.space - Fleet Carrier Management System')
    embed.set_timestamp()
    return send_webhook(webhook_url, 'Carrier Route announced', hooktype='discord', myembed=embed)


def announce_jump(request, cid, target, webhook_url, body=None):
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cid).one_or_none()
    embed = DiscordEmbed(title='Frame Shift Drive Charging',
                         description=f'{mycarrier.callsign} {util.from_hex(mycarrier.name)} is jumping.', color=242424,
                         url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    embed.set_author(name='Fleetcarrier.space', url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    if extra:
        embed.set_image(url=request.storage.url(extra.carrier_image))
    else:
        embed.set_image(url='https://fleetcarrier.space/static/img/carrier_default.png')
    embed.set_footer(text='Fleetcarrier.space - Fleet Carrier Management System')
    embed.add_embed_field(name='Departing from', value=mycarrier.currentStarSystem)
    embed.add_embed_field(name='Headed to', value=target)
    if body:
        embed.add_embed_field(name='Orbiting ', value=body)
    embed.set_timestamp()
    return send_webhook(webhook_url, 'Carrier Jump scheduled', hooktype='discord', myembed=embed)


def cancel_jump(request, cid, webhook_url, override=False):
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cid).one_or_none()
    embed = DiscordEmbed(title='Jump Cancelled',
                         description=f'{util.from_hex(mycarrier.name)} has cancelled jump.', color=242424,
                         url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    embed.set_author(name='Fleetcarrier.space', url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    if extra:
        embed.set_image(url=request.storage.url(extra.carrier_image))
    else:
        embed.set_image(url='https://fleetcarrier.space/static/img/carrier_default.png')
    if override:
        embed.set_image(url='https://media.giphy.com/media/B9NG8QJWN6pnG/giphy.gif')
    embed.set_footer(text='Fleetcarrier.space - Fleet Carrier Management System')
    embed.add_embed_field(name='Staying right here in ', value=mycarrier.currentStarSystem)
    embed.set_timestamp()
    return send_webhook(webhook_url, 'Carrier Jump cancelled', hooktype='discord', myembed=embed)


def calendar_event(request, calendar_id, webhook_url):
    """

    :param request:
    :param calendar_id:
    :param webhook_url:
    :return:
    """
    cdata = request.dbsession.query(Calendar).filter(Calendar.id == calendar_id).one_or_none()
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cdata.carrier_id).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cdata.carrier_id).one_or_none()
    if not cdata:
        return None
    embed = DiscordEmbed(title='Event Scheduled',
                         description=f'{mycarrier.callsign} {util.from_hex(mycarrier.name)} has scheduled an event.',
                         color=242424,
                         url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    embed.set_author(name='Fleetcarrier.space', url=f'https://fleetcarrier.space/carrier/{mycarrier.callsign}')
    if extra:
        embed.set_image(url=request.storage.url(extra.carrier_image))
    else:
        embed.set_image(url='https://fleetcarrier.space/static/img/carrier_default.png')
    embed.set_footer(text='Fleetcarrier.space - Fleet Carrier Management System')
    embed.add_embed_field(name='Starting at', value=str(cdata.start))
    embed.add_embed_field(name='Ending at', value=str(cdata.end))
    embed.add_embed_field(name='Title', value=str(cdata.title))
    embed.set_timestamp()
    return send_webhook(webhook_url, 'Carrier Jump scheduled', hooktype='discord', myembed=embed)


def get_webhooks(request, cid):
    """
    Checks whether a carrier has associated webhooks
    :param request: The request object
    :param cid: Carrier ID
    :return: A list of webhooks, or false if none are set.
    """
    hooks = request.dbsession.query(Webhook).filter(or_(Webhook.carrier_id == cid, Webhook.isGlobal)).all()
    if hooks:
        data = []
        for row in hooks:
            print(f"Getting webhook, row events {row.calendarEvents}")
            data.append(
                {'webhook_url': row.hook_url, 'webhook_type': row.hook_type, 'calendarEvents': row.calendarEvents,
                 'jumpEvents': row.jumpEvents, 'marketEvents': row.marketEvents})
        return data
    else:
        return False
