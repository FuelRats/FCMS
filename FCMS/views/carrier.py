from datetime import datetime, timedelta

from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier, itinerary, cargo, ship, module, market
from ..utils import capi
from ..utils import util
from ..utils import carrier_data


@view_config(route_name='carrier_subview', renderer='../templates/my_carrier.jinja2')
def carrier_subview(request):
    return


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
            return {
                    'sidebar_navlinks': True,
                    'sidebar_treeview': True,
                    'cmdr_name': 'Absolver',
                    'callsign': mycarrier.callsign,
                    'name': util.from_hex(mycarrier.name),
                    'fuel': mycarrier.fuel,
                    'current_system': mycarrier.currentStarSystem,
                    'last_updated': mycarrier.lastUpdated,
                    'ships': jcarrier['ships']['shipyard_list'].items() if jcarrier['ships']['shipyard_list'] else {},
                    'itinerary': jcarrier['itinerary']['completed'] or {},
                    'market': jcarrier['market']['commodities'] or {},
                    'modules': jcarrier['modules'].items() if jcarrier['modules'] else {},
            }
        shp = request.dbsession.query(ship.Ship).filter(ship.Ship.carrier_id == mycarrier.id)
        ships = {}
        for sp in shp:
            ships[sp.name] = {'name': sp.name, 'ship_id': sp.ship_id, 'basevalue': sp.basevalue,
                                'stock': sp.stock}
        iti = request.dbsession.query(itinerary.Itinerary).filter(itinerary.Itinerary.carrier_id == mycarrier.id)
        its = []
        for it in iti:
            its.append({"departureTime": it.departureTime, 'arrivalTime': it.arrivalTime,
                          'visitDurationSeconds': it.visitDurationSeconds,
                          'starsystem': it.starsystem})
        mkq = request.dbsession.query(market.Market).filter(market.Market.carrier_id == mycarrier.id)
        mkt = []
        for it in mkq:
            mkt.append({'id': it.commodity_id, 'categoryname': it.categoryname, 'name': it.name,
                        'stock': it.stock, 'buyPrice': it.buyPrice, 'sellPrice': it.sellPrice,
                        'demand': it.demand})

        mdq = request.dbsession.query(module.Module).filter(module.Module.carrier_id == mycarrier.id)
        mods = {}
        for md in mdq:
            mods[md.id] = {'id': md.module_id, 'category': md.category, 'name': md.name,
                           'cost': md.cost, 'stock': md.stock}

        return {
            'callsign': mycarrier.callsign,
            'name': util.from_hex(mycarrier.name),
            'fuel': mycarrier.fuel,
            'current_system': mycarrier.currentStarSystem,
            'last_updated': mycarrier.lastUpdated,
            'ships': ships.items(),
            'itinerary': iti,
            'market': mkt,
            'modules': mods.items()
        }

    else:
        print("No such carrier!")
