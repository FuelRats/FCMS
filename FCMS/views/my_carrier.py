from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier
from ..utils import capi
from ..utils import util
from ..utils import user as usr


@view_config(route_name='my_carrier', renderer='../templates/my_carrier.jinja2')
def mycarrier_view(request):
    user = request.user
    userdata = usr.populate_user(request)
    if user:
        mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.owner == user.id).one_or_none()
        if not mycarrier:
            print("No carrier for that user!")
            return {'user': userdata, 'error': 'no carrier!'}
        return {
            'user': userdata,
            'callsign': mycarrier.callsign,
            'name': util.from_hex(mycarrier.name),
            'fuel': mycarrier.fuel,
            'current_system': mycarrier.currentStarSystem,
            'last_updated': mycarrier.lastUpdated
        }
