from datetime import datetime, timedelta

from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier, itinerary, cargo, ship, module, market
from ..utils import capi
from ..utils import util
from ..utils import carrier_data


@view_config(route_name='carrier_subview', renderer='../templates/carrier_subview.jinja2')
def carrier_subview(request):
    cid = request.dbsession.query(carrier.Carrier). \
        filter(carrier.Carrier.callsign == request.matchdict['cid']).one_or_none()
    view = request.matchdict['subview']
    data = []
    if view in ['shipyard', 'itinerary', 'market', 'outfitting']:
        headers, data = carrier_data.populate_subview(request, cid.id, view)
    print(f"data: {data}")
    return {'callsign': cid.callsign,
            'name': util.from_hex(cid.name),
            'sidebar_treeview': True,
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
            'items': data}


@view_config(route_name='carrier', renderer='../templates/my_carrier.jinja2')
def carrier_view(request):
    cid = request.matchdict['cid']
    mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.callsign == cid).one_or_none()
    if mycarrier:
        print("Yep, I have a carrier like that.")
        last = mycarrier.lastUpdated
        print(f"Last: {last}")
        print(f"Delta: {datetime.now() - timedelta(hours=2)}")
        if not last:
            last = datetime.now() - timedelta(hours=3)  # Cheap hack to sort out missing lastUpdated.
        if last < datetime.now() - timedelta(minutes=2):
            print("Old carrier data, refresh!")
            jcarrier = carrier_data.update_carrier(request, mycarrier.id, user)
            if not jcarrier:
                print("Carrier update failed. Present old data.")
                return carrier_data.populate_view(request, mycarrier.id, user)
        return carrier_data.populate_view(request, mycarrier.id, user)

    else:
        print("No such carrier!")
