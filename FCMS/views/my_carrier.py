import os
from binascii import hexlify
from datetime import datetime, timedelta

from pyramid.view import view_config

import pyramid.httpexceptions as exc
from pyramid_storage.exceptions import FileNotAllowed

from ..models import carrier, CarrierExtra, Calendar, Webhook

from ..utils import carrier_data
from ..utils import menu, user as usr, webhooks
from humanfriendly import format_timespan
import logging

log = logging.getLogger(__name__)


@view_config(route_name='my_carrier', renderer='../templates/my_carrier.jinja2')
def mycarrier_view(request):
    if request.POST:
        if 'discord_webhook' in request.POST:
            # Got a new Discord webhook
            mycarrier = request.dbsession.query(carrier.Carrier).filter(
                carrier.Carrier.owner == request.user.id).one_or_none()
            newhook = Webhook(owner_id=request.user.id, carrier_id=mycarrier.id,
                              hook_url=request.POST['discord_webhook'],
                              hook_type='discord', enabled=True)
            request.dbsession.add(newhook)
        if 'eventtype' in request.POST:
            # Got a calendar event.
            starttime = datetime.fromisoformat(request.POST['starttime'])
            if 'endtime' in request.POST and request.POST['endtime'] != '':
                endtime = datetime.fromisoformat(request.POST['endtime'])
            else:
                endtime = starttime
            print(request.POST)
            if 'allday' in request.POST:
                allday = True if 'allday' == 'on' else False
            else:
                allday = False
            if request.POST['eventtype'] == 'scheduled_jump':
                print("In scheduled jump newevent.")
                newevent = Calendar(carrier_id=request.POST['cid'], owner_id=request.POST['owner_id'],
                                    title=request.POST['title'], start=starttime, end=endtime,
                                    allday=allday, fgcolor="#00AA00", bgcolor="#00FF00",
                                    departureSystem=request.POST['departureSystem'],
                                    arrivalSystem=request.POST['arrivalSystem'])
            else:
                print("In calendar newevent.")
                newevent = Calendar(carrier_id=request.POST['cid'], owner_id=request.POST['owner_id'],
                                    title=request.POST['title'], start=starttime, end=endtime,
                                    allday=allday, fgcolor="#00AA00", bgcolor="#00FF00")
            request.dbsession.add(newevent)
            mycarrier = request.dbsession.query(carrier.Carrier).filter(
                carrier.Carrier.owner == request.user.id).one_or_none()
            hooks = webhooks.get_webhooks(request, mycarrier.id)
            request.dbsession.flush()
            request.dbsession.refresh(newevent)
            if hooks:
                for hook in hooks:
                    log.debug(f"Process hook {hook['webhook_url']}")
                    if hook['webhook_type'] == 'discord':
                        if request.POST['eventtype'] == 'scheduled_jump':
                            res = webhooks.schedule_jump(request, newevent.id, hook['webhook_url'])
                            log.debug(f"Hook result: {res}")
                        else:
                            webhooks.calendar_event(request, newevent.id, hook['webhook_url'])

        if 'myfile' in request.POST:
            mycarrier = request.dbsession.query(carrier.Carrier). \
                filter(carrier.Carrier.owner == request.user.id).one_or_none()
            try:
                filename = request.storage.save(request.POST['myfile'], folder=f'carrier-{mycarrier.id}',
                                                randomize=True)
                log.debug(f"Filename pre storage: {filename}")
                cex = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == mycarrier.id).one_or_none()
                if not cex:
                    log.info(f"Adding new carrier image for {mycarrier.callsign}.")
                    nc = CarrierExtra(cid=mycarrier.id, carrier_image=filename)
                    request.dbsession.add(nc)
                else:
                    request.storage.delete(cex.carrier_image)
                    log.info(f"Updated carrier image for {mycarrier.callsign}")
                    cex.carrier_image = filename
            except FileNotAllowed:
                log.error(f"Attempt to upload invalid file by user {request.user.username} from {request.client_addr}")
                request.session.flash('Sorry, this file is not allowed.')
                return exc.HTTPSeeOther(request.route_url('my_carrier'))
    userdata = usr.populate_user(request)
    if request.user:
        # Debugging backdoor to other CMDRs my_carrier view.
        try:
            if request.user.userlevel > 4 and 'emulate' in request.params:
                mycarrier = request.dbsession.query(carrier.Carrier). \
                    filter(carrier.Carrier.callsign == request.params['emulate']).one_or_none()
            else:
                mycarrier = request.dbsession.query(carrier.Carrier).filter(
                    carrier.Carrier.owner == request.user.id).one_or_none()
        except AttributeError:
            return exc.HTTPFound("/login")
        if not mycarrier:
            # if user.no_carrier:
            #    return {'user': userdata, 'nocarrier': True}
            # log.warning(f"Attempt to access nonexistant own carrier by {user.username}")
            request.user.no_carrier = True
            return {'user': userdata, 'error': 'no carrier!', 'sidebar': menu.populate_sidebar(request)}
        last = mycarrier.lastUpdated
        # log.debug(f"Last update for carrier {cid}: {last}")
        if not last:
            last = datetime.now() - timedelta(minutes=20)  # Cheap hack to sort out missing lastUpdated.
        if last < datetime.now() - timedelta(minutes=15):
            log.debug(f"Refreshing data for {mycarrier.callsign}")
            jcarrier = carrier_data.update_carrier(request, mycarrier.id, request.user)
            if not jcarrier:
                log.warning(f"Carrier update failed for CID {mycarrier.callsign}. Presenting old data.")
        if not request.user.apiKey:
            request.user.apiKey = hexlify(os.urandom(64)).decode()
        finances = carrier_data.get_finances(request, mycarrier.id)
        data = carrier_data.populate_view(request, mycarrier.id, request.user)
        events = carrier_data.populate_calendar(request, mycarrier.id)
        crew = carrier_data.get_crew(request, mycarrier.id)
        cargo = carrier_data.get_cargo(request, mycarrier.id)
        data['view'] = 'My Carrier'
        data['finance'] = finances
        data['calendar'] = True
        data['formadvanced'] = True
        data['events'] = events
        data['crew'] = crew
        data['cargo'] = cargo
        data['apiKey'] = request.user.apiKey
        data['sidebar'] = menu.populate_sidebar(request)
        data['funding_time'] = format_timespan(int(int(mycarrier.balance) /
                                                   int(int(mycarrier.servicesCost) + int(mycarrier.coreCost)) * 604800)) \
            if int(
            mycarrier.balance) > 0 else f'DEBT DECOMMISSION IN {format_timespan(int(300000000 / int(mycarrier.servicesCost + mycarrier.coreCost) * 604800))}'
        return data
    raise exc.HTTPFound(request.route_url('login'))
