from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from pyramid_storage.exceptions import FileNotAllowed

from ..models import user, carrier, CarrierExtra
from ..utils import capi
from ..utils import util, carrier_data
from ..utils import menu, user as usr
from humanfriendly import format_timespan
import logging

log = logging.getLogger(__name__)


@view_config(route_name='my_carrier', renderer='../templates/my_carrier.jinja2')
def mycarrier_view(request):
    global user
    if request.POST:
        user = request.user
        if request.POST['myfile'].file:
            mycarrier = request.dbsession.query(carrier.Carrier).\
                filter(carrier.Carrier.owner == user.id).one_or_none()
            try:
                filename = request.storage.save(request.POST['myfile'], folder=f'carrier-{mycarrier.id}', randomize=True)
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
                log.error(f"Attempt to upload invalid file by user {user.username} from {request.client_addr}")
                request.session.flash('Sorry, this file is not allowed.')
                return exc.HTTPSeeOther(request.route_url('my_carrier'))
    userdata = usr.populate_user(request)
    mycarrier = None
    if user:
        # Debugging backdoor to other CMDRs my_carrier view.
        try:
            if user.userlevel > 4 and 'emulate' in request.params:
                mycarrier = request.dbsession.query(carrier.Carrier). \
                    filter(carrier.Carrier.callsign == request.params['emulate']).one_or_none()
            else:
                mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.owner == user.id).one_or_none()
        except AttributeError:
            return exc.HTTPFound("/login")
        if not mycarrier:
            if user.no_carrier:
                return {'user': userdata, 'nocarrier': True}
            log.warning(f"Attempt to access nonexistant own carrier by {user.username}")
            user.no_carrier = True
            return {'user': userdata, 'error': 'no carrier!'}
        finances = carrier_data.get_finances(request, mycarrier.id)
        data = carrier_data.populate_view(request, mycarrier.id, user)
        events = carrier_data.populate_calendar(request, mycarrier.id)
        crew = carrier_data.get_crew(request, mycarrier.id)
        cargo = carrier_data.get_cargo(request, mycarrier.id)
        data['finance'] = finances
        data['calendar'] = True
        data['formadvanced'] = True
        data['events'] = events
        data['crew'] = crew
        data['cargo'] = cargo
        data['sidebar'] = menu.populate_sidebar(request)
        data['funding_time'] = format_timespan(int(mycarrier.balance /
                                                   int(mycarrier.servicesCost + mycarrier.coreCost) * 604800)) \
            if mycarrier.balance > 0 else f'DEBT DECOMMISSION IN {format_timespan(int(300000000 / int(mycarrier.servicesCost + mycarrier.coreCost) * 604800))}'
        return data
    raise exc.HTTPFound(request.route_url('login'))
