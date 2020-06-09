from datetime import datetime, timedelta
from pyramid.view import view_config
from ..models import user, carrier
from ..utils import util, carrier_data, menu, user as usr
import logging

log = logging.getLogger(__name__)


@view_config(route_name='carrier_subview', renderer='../templates/carrier_subview.jinja2')
def carrier_subview(request):
    cid = request.dbsession.query(carrier.Carrier). \
        filter(carrier.Carrier.callsign == request.matchdict['cid']).one_or_none()
    data = []
    userdata = usr.populate_user(request)
    mymenu = menu.populate_sidebar(request)
    # log.debug(f"Populated menu: {menu.populate_sidebar(request)}")
    if not cid:
        log.error(f"Attempt to call subview for invalid carrier: {cid}")
        return {'error': 'Invalid carrier.', 'sidebar': mymenu, 'user': userdata}
    owner = request.dbsession.query(user.User).filter(user.User.id == cid.owner).one_or_none()
    if not owner:
        log.debug(f"No owner for carrier {cid}. Fake it.")
        owner = user.User(cmdr_name='Unknown CMDR')
    view = request.matchdict['subview']
    if view in ['shipyard', 'itinerary', 'market', 'outfitting', 'calendar']:
        headers, data = carrier_data.populate_subview(request, cid.id, view)
    log.debug(f"Carrier subview data for {cid}: {data}")
    events = carrier_data.populate_calendar(request, cid.id)
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
            'events': events,
            'sidebar': mymenu}


@view_config(route_name='carrier', renderer='../templates/carrier.jinja2')
def carrier_view(request):
    cid = request.matchdict['cid']
    userdata = usr.populate_user(request)
    mymenu = menu.populate_sidebar(request)
    mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.callsign == cid).one_or_none()
    if mycarrier:
        last = mycarrier.lastUpdated
        log.debug(f"Last update for carrier {cid}: {last}")
        if not last:
            last = datetime.now() - timedelta(minutes=20)  # Cheap hack to sort out missing lastUpdated.
        if last < datetime.now() - timedelta(minutes=15):
            log.debug(f"Refreshing data for {cid}")
            jcarrier = carrier_data.update_carrier(request, mycarrier.id, user)
            if not jcarrier:
                log.warning(f"Carrier update failed for CID {cid}. Presenting old data.")
                return carrier_data.populate_view(request, mycarrier.id, user)
        return carrier_data.populate_view(request, mycarrier.id, user)

    else:
        log.warning(f"Attempt to call carrier view with an invalid carrier reference {cid}")
        return {
            'user': userdata,
            'error': "No such carrier!",
            'sidebar': mymenu
        }

