import numpy
from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from sqlalchemy import text

from ..models import user, carrier
from ..utils import capi, sapi, util, menu
from ..utils import user as myuser
import re
import logging

log = logging.getLogger(__name__)


def fill_data(candidates, source):
    items = []
    for row in candidates:
        target = numpy.array((row.x, row.y, row.z))
        dist = numpy.linalg.norm(source - target)
        if row.taxation:
            taxcolor = "#00AA000" if row.taxation == 0 else "#DAD55E" if 25 > row.taxation > 0 \
                else "#FFC4505F" if 50 > row.taxation > 26 else "#FF0000"
        else:
            taxcolor = "#555555"
        items.append({'col1_svg': 'inline_svgs/state.jinja2', 'col1': util.from_hex(row.name),
                      'col2': row.callsign,
                      'is_DSSA': row.isDSSA,
                      'col3': row.currentStarSystem, 'col4': round(dist, 2),
                      'services': [{'color': '#00A000' if row.hasShipyard else '#FF0000',
                                    'svg': 'inline_svgs/shipyard.jinja2',
                                    'title': f'Shipyard {"" if row.hasShipyard else "NOT"} available'},
                                   {'color': '#00A000' if row.hasOutfitting else '#FF0000',
                                    'svg': 'inline_svgs/outfitting.jinja2',
                                    'title': f'Outfitting {"" if row.hasOutfitting else "NOT"} available'},
                                   {'color': '#00A000' if row.hasRepair else '#FF0000',
                                    'svg': 'inline_svgs/repair.jinja2',
                                    'title': f'Repair {"" if row.hasRepair else "NOT"} available'},
                                   {'color': '#00A000' if row.hasRefuel else '#FF0000',
                                    'svg': 'inline_svgs/refuel.jinja2',
                                    'title': f'Refueling {"" if row.hasRefuel else "NOT"} available'},
                                   {'color': '#00A000' if row.hasRearm else '#FF0000',
                                    'svg': 'inline_svgs/rearm.jinja2',
                                    'title': f'Rearming {"" if row.hasRearm else "NOT"} available'},
                                   {'color': '#00A000' if row.hasExploration else '#FF0000',
                                    'svg': 'inline_svgs/exploration.jinja2',
                                    'title': f'Interstellar Cartography {"" if row.hasExploration else "NOT"} available'},
                                   {'color': '#00A000' if row.hasVoucherRedemption else '#FF0000',
                                    'svg': 'inline_svgs/voucher_redemption.jinja2',
                                    'title': f'Interstellar Factor {"" if row.hasVoucherRedemption else "NOT"}  available'},
                                   {'color': '#00A000' if row.hasBlackMarket else '#FF0000',
                                    'svg': 'inline_svgs/blackmarket.jinja2',
                                    'title': f'Black Market {"" if row.hasBlackMarket else "NOT"} available'},
                                   {'color': '#00A000' if row.notoriousAccess else '#FF0000',
                                    'svg': 'inline_svgs/notorious_access.jinja2',
                                    'title': f'Notorious Commanders can {"" if row.notoriousAccess else "NOT"} dock'},
                                   {'color': '#00A000' if row.dockingAccess == 'all' else '#dad55e',
                                    'svg': 'inline_svgs/docking_access.jinja2',
                                    'title': f'Docking available for {"Squadron and Friends" if row.dockingAccess == "squadronfriends" else row.dockingAccess}'},
                                   {'color': taxcolor, 'svg': 'inline_svgs/taxation.jinja2',
                                    'title': f'Taxation is {row.taxation}%'}
                                   ]})
    return items


# TODO: This shit is nuts and needs to die in a fire. FIX IT!
@view_config(route_name='search', renderer='../templates/search.jinja2')
def search_view(request):
    term = request.params['term'] if 'term' in request.params else None
    userdata = {}
    mymenu = menu.populate_sidebar(request)
    coords = sapi.get_coords(term)
    x = coords['x']
    y = coords['y']
    z = coords['z']
    source = numpy.array((x, y, z))
    items = []
    cube = 5000
    if request.user:
        userdata = myuser.populate_user(request)
    else:
        userdata = {'cmdr_name': 'Not logged in', 'cmdr_image': '/static/dist/img/avatar.png', 'link': '/login'}
    if 'searchform' in request.params:
        return {'searchform': True, 'user': userdata, 'sidebar': mymenu}

    if 'dssa' in request.params:
        candidates = request.dbsession.query(carrier.Carrier).from_statement(
            text(f"SELECT *, (sqrt((cast(carriers.x AS FLOAT) - {x}"
                 f")^2 + (cast(carriers.y AS FLOAT) - {y}"
                 f")^2 + (cast(carriers.z AS FLOAT) - {z}"
                 f")^2)) as Distance from carriers where"
                 f" carriers.\"isDSSA\" is TRUE order by Distance"))
        items = fill_data(candidates, source)
        return {'view': 'DSSA Carriers', 'user': userdata, 'col1_header': 'Carrier', 'col2_header': 'Callsign', 'col3_header': 'System',
                'col4_header': 'Distance', 'items': items, 'result_header': f'DSSA Carriers',
                'carrier_search': True, 'sidebar': mymenu}
    if 'type' in request.params:
        if request.params['type'].lower() == 'closest':
            usr = capi.get_cmdr(request.user)
            if not usr:
                sys = 'Sol'
            else:
                sys = usr['lastSystem']['name']
            coords = sapi.get_coords(sys)
            x = coords['x']
            y = coords['y']
            z = coords['z']
            source = numpy.array((x, y, z))
            candidates = request.dbsession.query(carrier.Carrier).from_statement(
                text(f"SELECT *, (sqrt((cast(carriers.x AS FLOAT) - {x}"
                     f")^2 + (cast(carriers.y AS FLOAT) - {y}"
                     f")^2 + (cast(carriers.z AS FLOAT) - {z}"
                     f")^2)) as Distance from carriers where cast(carriers.x AS FLOAT) BETWEEN "
                     f"{str(float(x) - cube)} AND {str(float(x) + cube)}"
                     f" AND cast(carriers.y AS FLOAT) BETWEEN {str(float(y) - cube)} AND {str(float(y) + cube)}"
                     f" AND cast(carriers.z as FLOAT) BETWEEN {str(float(z) - cube)} AND {str(float(z) + cube)}"
                     f" order by Distance LIMIT 25"))
            items = fill_data(candidates, source)
            return {'user': userdata, 'col1_header': 'Carrier', 'col2_header': 'Callsign', 'col3_header': 'System',
                    'col4_header': 'Distance', 'items': items, 'result_header': f'carriers near {sys}',
                    'carrier_search': True, 'sidebar': mymenu, 'view': 'Closest Carriers'}

    if 'system' in request.params:
        # We're asking for a system name, so do a distance search.
        coords = sapi.get_coords(term)
        x = coords['x']
        y = coords['y']
        z = coords['z']
        source = numpy.array((x, y, z))
        items = []
        cube = 5000
        if coords:
            candidates = None
            if 'DSSA' in request.params:
                cand = request.dbsession.query(carrier.Carrier).from_statement(
                    text(f"SELECT *, (sqrt((cast(carriers.x AS FLOAT) - {x}"
                         f")^2 + (cast(carriers.y AS FLOAT) - {y}"
                         f")^2 + (cast(carriers.z AS FLOAT) - {z}"
                         f")^2)) as Distance from carriers where cast(carriers.x AS FLOAT) BETWEEN "
                         f"{str(float(x) - cube)} AND {str(float(x) + cube)}"
                         f" AND cast(carriers.y AS FLOAT) BETWEEN {str(float(y) - cube)} AND {str(float(y) + cube)}"
                         f" AND cast(carriers.z as FLOAT) BETWEEN {str(float(z) - cube)} AND {str(float(z) + cube)}"
                         f" AND carriers.\"isDSSA\" is TRUE order by Distance"))
            else:
                cand = request.dbsession.query(carrier.Carrier).from_statement(
                    text(f"SELECT *, (sqrt((cast(carriers.x AS FLOAT) - {x}"
                         f")^2 + (cast(carriers.y AS FLOAT) - {y}"
                         f")^2 + (cast(carriers.z AS FLOAT) - {z}"
                         f")^2)) as Distance from carriers where cast(carriers.x AS FLOAT) BETWEEN "
                         f"{str(float(x) - cube)} AND {str(float(x) + cube)}"
                         f" AND cast(carriers.y AS FLOAT) BETWEEN {str(float(y) - cube)} AND {str(float(y) + cube)}"
                         f" AND cast(carriers.z as FLOAT) BETWEEN {str(float(z) - cube)} AND {str(float(z) + cube)}"
                         f" order by Distance LIMIT 25")).all()
            items = fill_data(cand, source)
            return {'user': userdata, 'col1_header': 'Carrier', 'col2_header': 'Callsign', 'col3_header': 'System',
                    'col4_header': 'Distance', 'items': items, 'result_header': f'carriers near {term}',
                    'carrier_search': True, 'sidebar': mymenu, 'view': 'Carrier Search'}
    rs = '^[A-Za-z0-9]{3}-[A-Za-z0-9]{3}$'
    r = re.compile(rs)
    if r.search(term):
        # Looks like a carrier ID, let's see if we have it.
        res = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.callsign == term.upper()).one_or_none()
        if res:
            raise exc.HTTPFound(request.route_url(f'carrier', cid=term.upper()))
    res = request.dbsession.query(user.User).filter(user.User.cmdr_name.ilike(term))
    if res:
        if res.count() == 1:
            # Single CMDR name hit, go to their carrier.
            row = res.one()
            cx = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.owner == row.id).one_or_none()
            if cx:
                raise exc.HTTPFound(request.route_url(f'carrier', cid=cx.callsign))
            else:
                return {'error': 'Player does not have a carrier.'}
        elif res.count() > 1:
            for row in res:
                items.append({'col1': row.cmdr_name, 'col2': row.callsign, 'col3': row.system, 'col4': None})

    res = request.dbsession.query(carrier.Carrier). \
        filter(carrier.Carrier.name.like(f'%{util.to_hex(term.upper()).decode("utf8")}%'))
    print(f"Callsign: {term.upper()} Enc: {util.to_hex(term.upper()).decode('utf8')}")
    if res:
        if res.count() == 1:
            row = res.one()
            print(f"Matched {row.callsign}")
            raise exc.HTTPFound(request.route_url(f'carrier', cid=row.callsign))
        elif res.count() > 1:
            for row in res:
                print(f"Row: {row.callsign}")
        # We have a carrier name match!
    else:
        log.error(f"No match for search on term {term}")
        return {'error': f'No matches for your search term {term}'}
    return {'user': userdata, 'col1_header': 'Carrier', 'col2_header': 'Callsign', 'col3_header': 'System',
            'col4_header': 'Distance', 'view': 'Carrier search'}
