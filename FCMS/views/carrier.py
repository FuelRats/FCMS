from datetime import datetime, timedelta

from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier, itinerary, cargo, ship, module, market
from ..utils import capi
from ..utils import util
from ..utils import carrier_data
from ..utils import menu, user as usr


@view_config(route_name='carrier_subview', renderer='../templates/carrier_subview.jinja2')
def carrier_subview(request):
    cid = request.dbsession.query(carrier.Carrier). \
        filter(carrier.Carrier.callsign == request.matchdict['cid']).one_or_none()
    print(menu.populate_sidebar(request))
    owner = request.dbsession.query(user.User).filter(user.User.id == cid.owner).one_or_none()
    if not owner:
        print("No owner for carrier. Fake it.")
        owner = user.User(cmdr_name='Unknown CMDR')
    view = request.matchdict['subview']
    data = []
    userdata = usr.populate_user(request)
    mymenu = menu.populate_sidebar(request)
    if view in ['shipyard', 'itinerary', 'market', 'outfitting', 'calendar']:
        headers, data = carrier_data.populate_subview(request, cid.id, view)
    print(f"data: {data}")
    return {'user': userdata,
            'owner': owner.cmdr_name or "Unknown",
            'callsign': cid.callsign,
            'name': util.from_hex(cid.name),
            'current_view': view,
            'cmdr_image': '/static/dist/img/avatar.png',
            'shipyard': cid.hasShipyard,
            'outfitting': cid.hasOutfitting,
            'refuel': cid.hasRefuel,
            'rearm': cid.hasRearm,
            'repair': cid.hasRepair,
            'exploration': cid.hasExploration,
            'commodities': cid.hasCommodities,
            'black_market': cid.hasBlackMarket,
            'voucher_redemption': cid.hasVoucherRedemption,
            'col1_header': headers['col1_header'],
            'col2_header': headers['col2_header'],
            'col3_header': headers['col3_header'],
            'col4_header': headers['col4_header'],
            'items': data,
            'sidebar': mymenu}


@view_config(route_name='carrier', renderer='../templates/carrier.jinja2')
def carrier_view(request):
    cid = request.matchdict['cid']
    userdata = usr.populate_user(request)
    mymenu = menu.populate_sidebar(request)
    mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.callsign == cid).one_or_none()
    if mycarrier:
        last = mycarrier.lastUpdated
        print(f"Last: {last}")
        if not last:
            last = datetime.now() - timedelta(minutes=20)  # Cheap hack to sort out missing lastUpdated.
        if last < datetime.now() - timedelta(minutes=15):
            print("Old carrier data, refresh!")
            jcarrier = carrier_data.update_carrier(request, mycarrier.id, user)
            if not jcarrier:
                print("Carrier update failed. Present old data.")
                return carrier_data.populate_view(request, mycarrier.id, user)
        return carrier_data.populate_view(request, mycarrier.id, user)

    else:
        return {
            'user': userdata,
            'error': "No such carrier!",
            'sidebar': mymenu
        }

