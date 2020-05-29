from datetime import datetime, timedelta

from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier
from ..utils import capi
from ..utils import util


@view_config(route_name='carrier', renderer='../templates/my_carrier.jinja2')
def carrier_view(request):
    cid = request.matchdict['cid']
    mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.callsign == cid).one_or_none()
    if mycarrier:
        print("Yep, I have a carrier like that.")
        last = mycarrier.lastUpdated
        print(f"Last: {last}")
        print(f"Delta: {datetime.now() - timedelta(hours=2)}")
        if last < datetime.now() - timedelta(hours=2):
            print("Old carrier data, refresh!")
            owner = request.dbsession.query(user.User).filter(user.User.id == mycarrier.owner).one_or_none()
            if owner:
                jcarrier = capi.get_carrier(owner)
                print(f"New carrier: {jcarrier}")
                services = jcarrier['market']['services']
                mycarrier.owner = owner.id
                mycarrier.callsign = jcarrier['name']['callsign']
                mycarrier.name = jcarrier['name']['vanityName']
                mycarrier.currentStarSystem = jcarrier['currentStarSystem']
                mycarrier.balance = jcarrier['balance']
                mycarrier.fuel = jcarrier['fuel']
                mycarrier.state = jcarrier['state']
                mycarrier.theme = jcarrier['theme']
                mycarrier.dockingAccess = jcarrier['dockingAccess']
                mycarrier.notoriousAccess = jcarrier['notoriousAccess']
                mycarrier.totalDistanceJumped = jcarrier['itinerary']['totalDistanceJumpedLY']
                mycarrier.currentJump = jcarrier['itinerary']['currentJump']
                mycarrier.taxation = jcarrier['finance']['taxation']
                mycarrier.coreCost = jcarrier['finance']['coreCost']
                mycarrier.servicesCost = jcarrier['finance']['servicesCost']
                mycarrier.jumpsCost = jcarrier['finance']['jumpsCost']
                mycarrier.numJumps = jcarrier['finance']['numJumps']
                mycarrier.hasCommodities = True
                mycarrier.hasCarrierFuel = True
                mycarrier.hasRearm = True if services['rearm'] == 'ok' else False
                mycarrier.hasShipyard = True if services['shipyard'] == 'ok' else False
                mycarrier.hasOutfitting = True if services['outfitting'] == 'ok' else False
                mycarrier.hasBlackMarket = True if services['blackmarket'] == 'ok' else False
                mycarrier.hasVoucherRedemption = True if services['voucherredemption'] == 'ok' else False
                mycarrier.hasExploration = True if services['exploration'] == 'ok' else False
                mycarrier.lastUpdated = datetime.now()

        return {
            'callsign': mycarrier.callsign,
            'name': util.from_hex(mycarrier.name),
            'fuel': mycarrier.fuel,
            'current_system': mycarrier.currentStarSystem,
            'last_updated': mycarrier.lastUpdated
        }

    else:
        print("No such carrier!")
