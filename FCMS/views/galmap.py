from datetime import datetime, timedelta
from pyramid.view import view_config
from ..models import User, Carrier
from ..utils import util, carrier_data, menu, user as usr
import logging

from ..utils.util import from_hex

log = logging.getLogger(__name__)


@view_config(route_name='galmap', renderer='../templates/galmap.jinja2')
def carrier_subview(request):
    userdata = usr.populate_user(request)
    mymenu = menu.populate_sidebar(request)

    cs = request.dbsession.query(Carrier).all()
    pins = []
    for row in cs:
        if row.x == 0 and row.y == 0 and row.z == 0 or not row.z or not row.y or not row.x:
            continue
        pins.append({'title': f'{row.callsign} - {from_hex(row.name)} ({row.currentStarSystem})', 'x': row.x, 'y': row.y})
    print(pins)
    return {'map': {'pins': pins, 'focus': {'x': 0, 'y': 0, 'zoom': -5}}, 'user': userdata, 'sidebar': mymenu}

