# Various carrier data update convenience functions.
# AKA "Get all the ugly shit out of the views."
from datetime import datetime

from . import capi
from ..models import Carrier, User, Itinerary, Market, Module, Ship, Cargo
import pyramid.httpexceptions as exc
from ..utils import util
from humanfriendly import format_timespan


def populate_subview(request, cid, subview):
    """
    Populates a subview page's data.
    :param request: Request object (For DB access)
    :param cid: Carrier ID to populate
    :param subview: Which subview to fetch
    :return:
    """
    res = []
    headers = {}
    if subview == 'shipyard':
        ships = request.dbsession.query(Ship).filter(Ship.carrier_id == cid)
        for sp in ships:
           res.append({'col1_svg': 'inline_svgs/shipyard.jinja2', 'col1': sp.name, 'col2': sp.basevalue,
                       'col3': sp.stock, 'col4': '<i class="fas fa-search"></i>'})
        headers = {'col1_header': 'Name', 'col2_header': 'Value', 'col3_header': 'stock',
                   'col4_header': 'Coriolis'}
    if subview == 'itinerary':
        itinerary = request.dbsession.query(Itinerary).filter(Itinerary.carrier_id == cid)
        for it in itinerary:
            res.append({'col1_svg': 'inline_svgs/completed_jumps.jinja2', 'col1': it.starsystem,
                        'col2': it.arrivalTime, 'col3': format_timespan(it.visitDurationSeconds),
                        'col4': it.departureTime})
        headers = {'col1_header': 'Star system', 'col2_header': 'Arrival time', 'col3_header': 'Visit duration',
                   'col4_header': 'Departure time'}
    if subview == 'market':
        market = request.dbsession.query(Market).filter(Market.carrier_id == cid)
        for mk in market:
            res.append({'col1_svg': 'inline_svgs/commodities.jinja2', 'col1': (mk.demand if mk.demand else mk.stock),
                        'col2': mk.name, 'col3': mk.buyPrice, 'col4': mk.sellPrice })
        headers = {'col1_header': 'Demand/Supply', 'col2_header': 'Commodity', 'col3_header': 'Buy price',
                   'col4_header': 'Sell price'}
    if subview == 'outfitting':
        module = request.dbsession.query(Module).filter(Module.carrier_id == cid)
        for md in module:
            res.append({'col1_svg': 'inline_svgs/outfitting.jinja2', 'col1': md.stock, 'col2': md.category,
                        'col3': md.name, 'col4': md.cost})
        headers = {'col1_header': 'Stock', 'col2_header': 'Category', 'col3_header': 'Name',
                   'col4_header': 'Cost'}

    return headers, res


def populate_view(request, cid, user):
    """
    Populates a dict with carrier data usable in the carrier views. Note: this does NOT fire a
    update request if the data is old, it populates ONLY from DB.
    :param request: The request object (For DB access)
    :param cid: Carrier ID to populate
    :param user: User executing the request.
    :return:
    """
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    ships = request.dbsession.query(Ship).filter(Carrier.id == cid)
    itinerary = request.dbsession.query(Itinerary).filter(Carrier.id == cid)
    market = request.dbsession.query(Market).filter(Carrier.id == cid)
    modules = request.dbsession.query(Module).filter(Carrier.id == cid)
    owner = request.dbsession.query(User).filter(User.id == mycarrier.owner).one_or_none()
    sps = {}
    for sp in ships:
        sps[sp.name] = {'name': sp.name, 'ship_id': sp.ship_id, 'basevalue': sp.basevalue,
                          'stock': sp.stock}
    its = []
    for it in itinerary:
        its.append({"departureTime": it.departureTime, 'arrivalTime': it.arrivalTime,
                    'visitDurationSeconds': it.visitDurationSeconds,
                    'starsystem': it.starsystem})
    mkt = []
    for it in market:
        mkt.append({'id': it.commodity_id, 'categoryname': it.categoryname, 'name': it.name,
                    'stock': it.stock, 'buyPrice': it.buyPrice, 'sellPrice': it.sellPrice,
                    'demand': it.demand})

    mods = {}
    for md in modules:
        mods[md.id] = {'id': md.module_id, 'category': md.category, 'name': md.name,
                       'cost': md.cost, 'stock': md.stock}

    return {
        'callsign': mycarrier.callsign,
        'name': util.from_hex(mycarrier.name),
        'fuel': mycarrier.fuel,
        'current_system': mycarrier.currentStarSystem,
        'last_updated': mycarrier.lastUpdated,
        'ships': sps.items() if sps else {},
        'itinerary': its or {},
        'market': mkt or {},
        'modules': mods.items() if sps else {},
        'balance': mycarrier.balance,
        'taxation': mycarrier.taxation,
        'distance_jumped': mycarrier.totalDistanceJumped,
        'capacity': mycarrier.capacity,
        'docking_access': mycarrier.dockingAccess,
        'notorious_access': mycarrier.notoriousAccess,
        'shipyard': mycarrier.hasShipyard,
        'outfitting': mycarrier.hasOutfitting,
        'refuel': mycarrier.hasRefuel,
        'rearm': mycarrier.hasRearm,
        'repair': mycarrier.hasRepair,
        'exploration': mycarrier.hasExploration,
        'commodities': mycarrier.hasCommodities,
        'black_market': mycarrier.hasBlackMarket,
        'voucher_redemption': mycarrier.hasVoucherRedemption,
        'maintenance': int(mycarrier.coreCost + mycarrier.servicesCost),
        'sidebar_treeview': True,
        'cmdr_name': owner.cmdr_name,
        'current_view': 'summary',
        'cmdr_image': '/static/dist/img/avatar.png'
    }


def update_carrier(request, cid, user):
    """
    Updates carrier data. If carrier update fails and the user owns the carrier in question, a new
    OAuth2 flow is initiated.
    :param request: The request object (For DB access)
    :param cid: Carrier ID to be updated
    :param user: The user executing the request
    :return: Updated carrier JSON (from CAPI) or None if failed and not same user.
    """
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
        if jcarrier['ships']['shipyard_list']:
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
        if jcarrier['modules']:
            for item, it in jcarrier['modules'].items():
                md = Module(carrier_id=mycarrier.id, category=it['category'],
                            name=it['name'], cost=it['cost'], stock=it['stock'],
                            module_id=it['id'])
                request.dbsession.add(md)
        return jcarrier or None
    return None
