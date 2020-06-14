# Various carrier data update convenience functions.
# AKA "Get all the ugly shit out of the views."
import json
from datetime import datetime

from . import capi
from ..models import Carrier, User, Itinerary, Market, Module, Ship, Cargo, Calendar, CarrierExtra
import pyramid.httpexceptions as exc
from ..utils import util, sapi, user as usr, menu
from humanfriendly import format_timespan, format_number
import logging

log = logging.getLogger(__name__)


def populate_calendar(request, cid):
    """
    Populates an event list for the calendar.
    :param request: The request object
    :param cid: Carrier ID
    :return: A dict of events.
    """
    carrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    if carrier:
        data = []
        print(f"CID is {cid}")
        calendar = request.dbsession.query(Calendar).filter(Calendar.carrier_id == carrier.id).all()
        for event in calendar:
            print(f"Process Calendar ID {event.id}")
            if event.url:
                data.append({'title': event.title,
                             'start': event.start,
                             'end': event.end,
                             'backgroundColor': event.bgcolor,
                             'borderColor': event.fgcolor,
                             'allday': event.allday,
                             'url': event.url
                             })
            else:
                data.append({'title': event.title,
                             'start': event.start,
                             'end': event.end,
                             'backgroundColor': event.bgcolor,
                             'borderColor': event.fgcolor,
                             'allday': event.allday,
                             })
        calendar = request.dbsession.query(Calendar).filter(Calendar.is_global).all()
        for event in calendar:
            print(f"Process Calendar ID {event.id}")
            if event.url:
                data.append({'title': event.title,
                             'start': event.start,
                             'end': event.end,
                             'backgroundColor': event.bgcolor,
                             'borderColor': event.fgcolor,
                             'allday': event.allday,
                             'url': event.url
                             })
            else:
                data.append({'title': event.title,
                             'start': event.start,
                             'end': event.end,
                             'backgroundColor': event.bgcolor,
                             'borderColor': event.fgcolor,
                             'allday': event.allday,
                             })

        return data


def get_finances(request, cid):
    """
    Gets the financial information for a carrier.
    :param request: The request object
    :param cid: Carrier ID
    :return: A dict of financial information
    """
    carrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    if carrier:
        cdata = None
        if not carrier.cachedJson:
            cdata = update_carrier(request, cid, request.user)
        else:
            cdata = json.loads(carrier.cachedJson)
        data = {}
        for key, val in cdata['finance'].items():
            data[key] = format_number(val)
        return data
    else:
        log.error("Attempt to get finances for non-existant carrier!")
        return None


def get_crew(request, cid):
    """
    Get crew information for a carrier.
    :param request: The request object
    :param cid: Carrier ID
    :return: A dict of crew info
    """
    carrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    if carrier:
        cdata = None
        if not carrier.cachedJson:
            cdata = update_carrier(request, cid, request.user)
        else:
            cdata = json.loads(carrier.cachedJson)
        return cdata['servicesCrew']
    else:
        log.error("Attempt to get crew for non-existant carrier!")
        return None


def get_cargo(request, cid):
    """
    Gets a carrier's cargo.
    :param request: Request object
    :param cid: Carrier ID
    :return: A list of dicts containing cargo info.
    """
    carrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    if carrier:
        clean_cargo = {}
        stolen_cargo = {}
        result = request.dbsession.query(Cargo).filter(Cargo.carrier_id == cid)
        for cg in result:
            if cg.stolen:
                if cg.commodity in stolen_cargo.keys():
                    stolen_cargo[cg.commodity]['quantity'] = stolen_cargo[cg.commodity]['quantity'] + cg.quantity
                else:
                    stolen_cargo[cg.commodity] = {'commodity': cg.commodity,
                                                  'quantity': cg.quantity,
                                                  'value': cg.value,
                                                  'stolen': cg.stolen,
                                                  'locname': cg.locName
                                                  }
            else:
                if cg.commodity in clean_cargo.keys():
                    clean_cargo[cg.commodity]['quantity'] = clean_cargo[cg.commodity]['quantity'] + cg.quantity
                else:
                    clean_cargo[cg.commodity] = {'commodity': cg.commodity,
                                                 'quantity': cg.quantity,
                                                 'value': cg.value,
                                                 'stolen': cg.stolen,
                                                 'locname': cg.locName
                                                 }
        data = {'clean_cargo': clean_cargo, 'stolen_cargo': stolen_cargo}
        return data


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
        mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
        if request.user:
            if mycarrier.showItinerary or mycarrier.owner == request.user.id or request.user.userlevel >= 4:
                itinerary = request.dbsession.query(Itinerary).filter(Itinerary.carrier_id == cid)
        elif mycarrier.showItinerary:
            itinerary = request.dbsession.query(Itinerary).filter(Market.carrier_id == cid)
        else:
            itinerary = []
        for it in itinerary:
            if it.categoryname != 'NonMarketable':
                res.append({'col1_svg': 'inline_svgs/completed_jumps.jinja2', 'col1': it.starsystem,
                            'col2': it.arrivalTime, 'col3': format_timespan(it.visitDurationSeconds),
                            'col4': it.departureTime})
        headers = {'col1_header': 'Star system', 'col2_header': 'Arrival time', 'col3_header': 'Visit duration',
                   'col4_header': 'Departure time'}
    if subview == 'market':
        mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
        if request.user:
            if mycarrier.showMarket or mycarrier.owner == request.user.id or request.user.userlevel >= 4:
                market = request.dbsession.query(Market).filter(Market.carrier_id == cid)
        elif mycarrier.showMarket:
            market = request.dbsession.query(Market).filter(Market.carrier_id == cid)
        else:
            market = []
        for mk in market:
            res.append({'col1_svg': 'inline_svgs/commodities.jinja2', 'col1': (mk.demand if mk.demand else mk.stock),
                        'col2': mk.name, 'col3': mk.buyPrice, 'col4': mk.sellPrice})
        headers = {'col1_header': 'Demand/Supply', 'col2_header': 'Commodity', 'col3_header': 'Buy price',
                   'col4_header': 'Sell price'}
    if subview == 'outfitting':
        module = request.dbsession.query(Module).filter(Module.carrier_id == cid)
        for md in module:
            res.append({'col1_svg': 'inline_svgs/outfitting.jinja2', 'col1': md.stock, 'col2': md.category,
                        'col3': md.name, 'col4': md.cost})
        headers = {'col1_header': 'Stock', 'col2_header': 'Category', 'col3_header': 'Name',
                   'col4_header': 'Cost'}
    if subview == 'calendar':
        headers = {'col1_header': "Not yet", 'col2_header': "Not yet", 'col3_header': 'Not yet',
                   'col4_header': "Not yet"}
        res.append({"col1_svg": 'inline_svgs/completed_jumps.jinja2', 'col1': 'Not yet', 'col2': 'Not yet',
                    'col3': 'Not yet', 'col4': 'But soon!'})
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
    userdata = usr.populate_user(request)
    mycarrier = request.dbsession.query(Carrier).filter(Carrier.id == cid).one_or_none()
    mymenu = menu.populate_sidebar(request)

    if mycarrier.trackedOnly:
        # We only have limited data, return a subset.
        data = {
            'user': userdata,
            'cid': mycarrier.id,
            'owner': 'Unknown CMDR',
            'view': f'Carrier {mycarrier.callsign}',
            'callsign': mycarrier.callsign or "XXX-XXX",
            'name': util.from_hex(mycarrier.name) or "Unknown",
            'fuel': mycarrier.fuel or 0,
            'current_system': mycarrier.currentStarSystem,
            'last_updated': mycarrier.lastUpdated or datetime.now(),
            'balance': mycarrier.balance or 0,
            'taxation': mycarrier.taxation or 0,
            'distance_jumped': mycarrier.totalDistanceJumped or 0,
            'capacity': mycarrier.capacity or 0,
            'docking_access': mycarrier.dockingAccess,
            'notorious_access': mycarrier.notoriousAccess,
            'shipyard': mycarrier.hasShipyard or False,
            'outfitting': mycarrier.hasOutfitting or False,
            'refuel': mycarrier.hasRefuel or False,
            'rearm': mycarrier.hasRearm or False,
            'repair': mycarrier.hasRepair or False,
            'exploration': mycarrier.hasExploration or False,
            'commodities': mycarrier.hasCommodities or False,
            'black_market': mycarrier.hasBlackMarket or False,
            'voucher_redemption': mycarrier.hasVoucherRedemption or False,
            'maintenance': 0,
            'carrier_image': "/static/img/carrier_default.png",
            'carrier_motd': "No MOTD set",
            'system': mycarrier.currentStarSystem,
            'arrived_at': mycarrier.lastUpdated,
            'og_meta': True,
            'x': mycarrier.x,
            'y': mycarrier.y,
            'z': mycarrier.z,
            'sidebar': mymenu,
        }
        return data
    owner = request.dbsession.query(User).filter(User.id == mycarrier.owner).one_or_none()
    extra = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cid).one_or_none()
    itinerary = request.dbsession.query(Itinerary).filter(Itinerary.carrier_id == cid)
    events = populate_calendar(request, cid)
    data = {
        'user': userdata,
        'cid': mycarrier.id,
        'view': f'Carrier {mycarrier.callsign}',
        'owner_id': owner.id,
        'owner': owner.cmdr_name,
        'callsign': mycarrier.callsign or "XXX-XXX",
        'name': util.from_hex(mycarrier.name) or "Unknown",
        'fuel': mycarrier.fuel or 0,
        'current_system': mycarrier.currentStarSystem,
        'last_updated': mycarrier.lastUpdated or datetime.now(),
        'balance': mycarrier.balance or 0,
        'taxation': mycarrier.taxation or 0,
        'distance_jumped': mycarrier.totalDistanceJumped or 0,
        'capacity': mycarrier.capacity or 0,
        'docking_access': mycarrier.dockingAccess,
        'notorious_access': mycarrier.notoriousAccess,
        'shipyard': mycarrier.hasShipyard or False,
        'outfitting': mycarrier.hasOutfitting or False,
        'refuel': mycarrier.hasRefuel or False,
        'rearm': mycarrier.hasRearm or False,
        'repair': mycarrier.hasRepair or False,
        'exploration': mycarrier.hasExploration or False,
        'commodities': mycarrier.hasCommodities or False,
        'black_market': mycarrier.hasBlackMarket or False,
        'voucher_redemption': mycarrier.hasVoucherRedemption or False,
        'maintenance': int(mycarrier.coreCost + mycarrier.servicesCost) or 0,
        'carrier_image': extra.carrier_image if extra else "/static/img/carrier_default.png",
        'carrier_motd': extra.carrier_motd if extra else "No MOTD set",
        'system': mycarrier.currentStarSystem,
        'og_meta': True,
        'x': mycarrier.x,
        'y': mycarrier.y,
        'z': mycarrier.z,
        'sidebar': mymenu,
        'events': events,
        'calendar': True,
    }
    row = itinerary.filter(Itinerary.departureTime == None).one_or_none()
    if row:
        data['arrival'] = row.arrivalTime
    return data


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
            log.warning("CAPI update call failed, retry OAuth if owner.")
            if not request.user:
                log.warning("Not logged in, can't refresh OAuth token.")
                return None
            if mycarrier.owner == request.user.id:
                log.warning("Carrier being viewed by owner, ask for OAuth refresh.")
                url, state = capi.get_auth_url()
                raise exc.HTTPFound(location=url)
            else:
                log.warning(f"Not same owner! {mycarrier.owner} vs {request.user.id}.")
                return None
        try:
            if mycarrier.callsign != jcarrier['name']['callsign']:
                log.error(f"Carrier callsign has changed! This should not happen! {mycarrier.callsign} "
                          f"stored, update has {jcarrier['name']['callsign']}. Refresh initiated by user {request.user.username}.")
                return None
        except KeyError:
            log.error(
                f"No callsign set on already existing carrier? Requested CID: {cid} new carrier: {jcarrier['name']['callsign']} ")
            return None
        log.info(f"New carrier: {jcarrier}")
        coords = sapi.get_coords(jcarrier['currentStarSystem'])
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
        mycarrier.hasRepair = True if services['repair'] == 'ok' else False
        mycarrier.hasRefuel = True if services['refuel'] == 'ok' else False
        if 'error' not in coords:
            mycarrier.x = coords['x']
            mycarrier.y = coords['y']
            mycarrier.z = coords['z']
        mycarrier.trackedOnly = False
        mycarrier.cachedJson = json.dumps(jcarrier)
        mycarrier.lastUpdated = datetime.now()
        request.dbsession.query(Itinerary).filter(Itinerary.carrier_id
                                                  == mycarrier.id).delete()
        for item in jcarrier['itinerary']['completed']:
            itm = Itinerary(carrier_id=mycarrier.id, starsystem=item['starsystem'],
                            departureTime=item['departureTime'], arrivalTime=item['arrivalTime'],
                            visitDurationSeconds=item['visitDurationSeconds'])
            request.dbsession.add(itm)
        request.dbsession.query(Cargo).filter(Cargo.carrier_id
                                              == mycarrier.id).delete()
        for item in jcarrier['cargo']:
            cg = Cargo(carrier_id=mycarrier.id, commodity=item['commodity'],
                       quantity=item['qty'], stolen=item['stolen'], locName=item['locName'], value=item['value'])
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
        if 'ships' in jcarrier:
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
