from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier
from ..utils import capi
from ..utils import util, carrier_data
from ..utils import menu, user as usr
from humanfriendly import format_timespan


@view_config(route_name='my_carrier', renderer='../templates/my_carrier.jinja2')
def mycarrier_view(request):
    user = request.user
    userdata = usr.populate_user(request)
    mycarrier = None
    if user:
        # Debugging backdoor to other CMDRs my_carrier view.
        if user.userlevel > 4 and 'emulate' in request.params:
            mycarrier = request.dbsession.query(carrier.Carrier). \
                filter(carrier.Carrier.callsign == request.params['emulate']).one_or_none()
        else:
            mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.owner == user.id).one_or_none()
        if not mycarrier:
            print("No carrier for that user!")
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
        data['funding_time'] = format_timespan(int(mycarrier.balance /
                                                   int(mycarrier.servicesCost + mycarrier.coreCost) * 604800)) \
            if mycarrier.balance > 0 else f'DEBT DECOMMISSION IN {format_timespan(int(300000000 / int(mycarrier.servicesCost + mycarrier.coreCost) * 604800))}'
        return data
