# Webhooks for carrier events. Can fire from EDDN hits or calendar create/delete events.

import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from ..models import Carrier, Calendar, CarrierExtra, Webhook
from ..utils import util


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


def discord_embed(request, cid, event):
    """
    Makes a discord embed of a message.
    :param request: The request object
    :param cid: Carrier ID
    :param event: The event dict (EventType, StartTime, EndTime, Description)
    :return: A Discord embed object
    """


def schedule_jump(request, calendar_id, webhook_url):
    """
    Fires a webhook for a jump calendar event.
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
                         description=f'{util.from_hex(mycarrier.name)} has scheduled a jump.', color=242424,
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


def announce_jump(request, cid, target, webhook_url, body=None):
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cid).one_or_none()
    embed = DiscordEmbed(title='Frame Shift Drive Charging',
                         description=f'{util.from_hex(mycarrier.name)} is jumping.', color=242424,
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


def cancel_jump(request, cid, webhook_url, override):
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
                         description=f'{util.from_hex(mycarrier.name)} has scheduled an event.', color=242424,
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
    hooks = request.dbsession.query(Webhook).filter(Webhook.carrier_id == cid).all()
    if hooks:
        data = []
        for row in hooks:
            data.append({'webhook_url': row.hook_url, 'webhook_type': row.hook_type})
        return data
    else:
        return False

