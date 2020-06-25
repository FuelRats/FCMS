import json

from pyramid.view import view_config

from ..models import Route, Carrier, User, CarrierExtra
from ..models.routes import RouteCalendar, Region
from ..utils import util, menu, user as myuser
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)


@view_config(route_name='routes', renderer='../templates/routes.jinja2')
def routes_view(request):
    active_routes = request.dbsession.query(RouteCalendar).filter(RouteCalendar.isActive == True).order_by(
        RouteCalendar.scheduled_departure)
    data = []
    userdata = myuser.populate_user(request)
    mymenu = menu.populate_sidebar(request)

    for rc in active_routes:
        rt = request.dbsession.query(Route).filter(Route.id == rc.route_id).one_or_none()
        cr = request.dbsession.query(Carrier).filter(Carrier.id == rt.carrier_id).one_or_none()
        co = request.dbsession.query(User).filter(User.id == cr.owner).one_or_none()
        sr = request.dbsession.query(Region).filter(Region.id == rt.start_region).one_or_none()
        dr = request.dbsession.query(Region).filter(Region.id == rt.end_region).one_or_none()
        data.append({'carrier_id': rc.id, 'route_id': rc.id, 'route_name': rt.route_name,
                     'route_startPoint': rt.startPoint if not rc.isReversed else rt.endPoint,
                     'route_endPoint': rt.endPoint if not rc.isReversed else rt.startPoint,
                     'carrier_callsign': cr.callsign, 'carrier_owner': co.cmdr_name,
                     'start_region': sr.name, 'end_region': dr.name,
                     'carrier_name': util.from_hex(cr.name),
                     'scheduled_departure': rc.scheduled_departure,
                     })
    return {'routes': data, 'user': userdata, 'sidebar': mymenu}


@view_config(route_name='route_view', renderer='../templates/routes.jinja2')
def route_view(request):
    userdata = myuser.populate_user(request)
    mymenu = menu.populate_sidebar(request)

    rc = request.dbsession.query(RouteCalendar).filter(RouteCalendar.id == request.matchdict['rid']).one_or_none()
    if rc:
        rt = request.dbsession.query(Route).filter(Route.id == rc.route_id).one_or_none()
        cr = request.dbsession.query(Carrier).filter(Carrier.id == rt.carrier_id).one_or_none()
        co = request.dbsession.query(User).filter(User.id == cr.owner).one_or_none()
        cx = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == cr.id).one_or_none()
        sr = request.dbsession.query(Region).filter(Region.id == rt.start_region).one_or_none()
        dr = request.dbsession.query(Region).filter(Region.id == rt.end_region).one_or_none()
        data = {
            'carrier_id': cr.id, 'carrier_callsign': cr.callsign, 'carrier_name': util.from_hex(cr.name),
            'carrier_ownerid': cr.owner, 'carrier_owner': co.cmdr_name, 'route_name': rt.route_name,
            'route_startPoint': rt.startPoint, 'route_endPoint': rt.endPoint, 'route_startregion': sr.name,
            'route_endregion': dr.name, 'route_waypoints': json.loads(rt.waypoints),
            'route_description': rt.description, 'current_waypoint': rc.currentWaypoint,
            'scheduled_departure': rc.scheduled_departure,
            'carrier_image': cx.carrier_image if cx else '/static/img/carrier_default.png',
            'carrier_motd': cx.carrier_motd if cx else '',
            'docking_access': cr.dockingAccess, 'notorious_access': cr.notoriousAccess,
            'taxation': cr.taxation
        }

        return {'route': data, 'user': userdata, 'sidebar': mymenu}
    log.error(f"Route not found? RID was {request.matchdict['rid']}")
    return {'error': 'Route not found', 'user': userdata, 'sidebar': mymenu}
