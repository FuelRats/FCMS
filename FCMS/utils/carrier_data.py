# Various carrier data update convenience functions.
# AKA "Get all the ugly shit out of the views."
from datetime import datetime

from . import capi
from ..models import Carrier, User, Itinerary, Market, Module, Ship, Cargo
import pyramid.httpexceptions as exc


def update_carrier(request, cid, user):
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    owner = request.dbsession.query(User).filter(User.id == mycarrier.owner).one_or_none()
    if owner:
        jcarrier = capi.get_carrier(owner)
        if not jcarrier:
            print("CAPI update call failed, retry OAuth if owner.")
            if mycarrier.owner == request.user.id:
                print("Same user, ask for OAuth refresh.")
                url, state = capi.get_auth_url()
                return exc.HTTPFound(location=url)
            else:
                print(f"Not same user! {mycarrier.owner} vs {request.user.id}.")
                return None
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
        request.dbsession.query(Itinerary).filter(Itinerary.carrier_id
                                                  == mycarrier.id).delete()
        for item in jcarrier['itinerary']['completed']:
            print(f"Adding {item['starsystem']}")
            itm = Itinerary(carrier_id=mycarrier.id, starsystem=item['starsystem'],
                            departureTime=item['departureTime'], arrivalTime=item['arrivalTime'],
                            visitDurationSeconds=item['visitDurationSeconds'])
            request.dbsession.add(itm)
        request.dbsession.query(Cargo).filter(Cargo.carrier_id
                                              == mycarrier.id).delete()
        for item in jcarrier['cargo']:
            cg = Cargo(carrier_id=mycarrier.id, commodity=item['commodity'],
                       quantity=item['qty'], stolen=item['stolen'], locName=item['locName'])
            request.dbsession.add(cg)
        request.dbsession.query(Market).filter(Market.carrier_id
                                               == mycarrier.id).delete()
        for item in jcarrier['market']['commodities']:
            mk = Market(carrier_id=mycarrier.id, commodity_id=item['id'],
                        categoryname=item['categoryname'], name=item['name'],
                        stock=item['stock'], buyPrice=item['buyPrice'],
                        sellPrice=item['sellPrice'], demand=item['demand'],
                        locName=item['locName'])
            request.dbsession.add(mk)
        request.dbsession.query(Ship).filter(Ship.carrier_id
                                             == mycarrier.id).delete()
        print(jcarrier['ships']['shipyard_list'])
        for item, it in jcarrier['ships']['shipyard_list'].items():
            print(item)
            print(it)
            sp = Ship(carrier_id=mycarrier.id, name=it['name'],
                      ship_id=it['id'], basevalue=it['basevalue'],
                      stock=it['stock'])
            request.dbsession.add(sp)
        request.dbsession.query(Module).filter(Module.carrier_id
                                               == mycarrier.id).delete()
        print(jcarrier['modules'])
        for item, it in jcarrier['modules'].items():
            md = Module(carrier_id=mycarrier.id, category=it['category'],
                        name=it['name'], cost=it['cost'], stock=it['stock'],
                        module_id=it['id'])
            request.dbsession.add(md)
        return jcarrier or None
    return None
