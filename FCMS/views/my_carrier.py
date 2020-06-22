import json
import os
from binascii import hexlify
from datetime import datetime, timedelta, time

import colander
from deform import widget, Form, ValidationFailure
from pyramid.view import view_config

import pyramid.httpexceptions as exc
from pyramid_storage.exceptions import FileNotAllowed

from ..models import carrier, CarrierExtra, Calendar, Webhook, Region, Route

from ..utils import carrier_data
from ..utils import menu, user as usr, webhooks
from humanfriendly import format_timespan
import logging

log = logging.getLogger(__name__)


def populate_routes(request, cid):
    routes = []
    route = request.dbsession.query(Route).filter(Route.carrier_id == cid)
    for rt in route:
        print(f"Populate {rt.route_name}")
        sr = request.dbsession.query(Region).filter(Region.id == rt.start_region).one()
        er = request.dbsession.query(Region).filter(Region.id == rt.end_region).one()
        routes.append({'name': rt.route_name, 'end': rt.endPoint,
                       'start': rt.startPoint, 'waypoints': json.loads(rt.waypoints), 'startRegion': sr.name,
                       'endRegion': er.name})
    return routes


@view_config(route_name='my_carrier_subview', renderer='../templates/my_carrier_subview.jinja2')
def carrier_subview(request):
    if not request.user:
        return exc.HTTPFound(request.route_url('login'))
    modal_data = None
    userdata = usr.populate_user(request)
    mymenu = menu.populate_sidebar(request)
    mycarrier = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.owner == request.user.id).one_or_none()
    if not mycarrier:
        return exc.HTTPFound(request.route_url('my_carrier'))
    if 'delete-event' in request.POST:
        event = request.dbsession.query(Calendar).filter(Calendar.id == request.POST['delete-event']).one_or_none()
        if event:
            if event.owner_id == request.user.id:
                request.dbsession.query(Calendar).filter(Calendar.id == request.POST['delete-event']).delete()
                request.dbsession.flush()
                modal_data = {'load_fire': {'icon': 'success', 'message': 'Calendar event deleted!'}}
    elif 'market-update' in request.POST:
        items = []
        for control in request.POST:
            if control.startswith('highlight'):
                items.append(control.split('-')[1])
        hooks = webhooks.get_webhooks(request, mycarrier.id)
        if hooks:
            for hook in hooks:
                log.debug(f"Process hook {hook['webhook_url']} type {hook['webhook_type']}")
                if hook['webhook_type'] == 'discord':
                    if hook['marketEvents']:
                        webhooks.market_update(request, mycarrier.id, items, webhook_url=hook['webhook_url'],
                                               message=request.POST['message'] if 'message' in request.POST else None)
                        modal_data = {'load_fire': {'icon': 'success', 'message': 'Market update sent!'}}
    # log.debug(f"Populated menu: {menu.populate_sidebar(request)}")
    view = request.matchdict['subview']
    if view == 'messages':
        data = carrier_data.populate_view(request, mycarrier.id, request.user)
        if modal_data:
            data['modal'] = modal_data

        data['formadvanced'] = True
        data['apiKey'] = request.user.apiKey
        data['sidebar'] = menu.populate_sidebar(request)
        data['subview'] = 'messages'
        data['current_view'] = 'messages'
        return data
    if view == 'calendar':
        data = carrier_data.populate_view(request, mycarrier.id, request.user)
        if modal_data:
            data['modal'] = modal_data

        data['calendar'] = carrier_data.populate_calendar(request, mycarrier.id)
        data['formadvanced'] = True
        data['apiKey'] = request.user.apiKey
        data['sidebar'] = menu.populate_sidebar(request)
        data['subview'] = 'calendar'
        data['current_view'] = 'calendar'
        return data
    if view == 'market':
        data = carrier_data.populate_view(request, mycarrier.id, request.user)
        if modal_data:
            data['modal'] = modal_data

        data['market'] = carrier_data.get_market(request, mycarrier.id)
        data['formadvanced'] = True
        data['apiKey'] = request.user.apiKey
        data['sidebar'] = menu.populate_sidebar(request)
        data['subview'] = 'market'
        data['current_view'] = 'market'
        return data
    if view == 'routes':
        choices = []
        routechoices = []
        for choice in request.dbsession.query(Region).all():
            choices.append((choice.id, choice.name))
        for route in request.dbsession.query(Route).filter(Route.carrier_id == mycarrier.id).all():
            print(f"Append {route.id} as {route.route_name}")
            routechoices.append((route.id, route.route_name))

        class ScheduleSchema(colander.Schema):
            selectroute = colander.SchemaNode(colander.Integer(),
                                              widget=widget.SelectWidget(values=routechoices),
                                              required=True, title='Select route')
            departure_time = colander.SchemaNode(colander.DateTime(),
                                                 widget=widget.DateTimeInputWidget(id='departuretime'),
                                                 required=True)
            reverse_route = colander.SchemaNode(colander.Boolean(),
                                                widget=widget.CheckboxWidget(id='reverseroute'), required=True,
                                                default=False)

        class WaypointSchema(colander.Schema):
            system = colander.SchemaNode(colander.String(),
                                         widget=widget.AutocompleteInputWidget(
                                             values='https://system.api.fuelrats.com/typeahead', min_length=3
                                         ), id='systemfield')
            duration = colander.SchemaNode(colander.Time(),
                                           widget=widget.TimeInputWidget(),
                                           title='Duration of stay', default=time(hour=0, minute=20))

        class WaypointSequence(colander.SequenceSchema):
            waypoints = WaypointSchema(title=None)

        class RouteSchema(colander.Schema):
            id = colander.SchemaNode(colander.Integer(),
                                     widget=widget.HiddenWidget(),
                                     required=False, default=None, missing=colander.drop)
            carrier_id = colander.SchemaNode(colander.Integer(),
                                             widget=widget.HiddenWidget(),
                                             required=True, default=mycarrier.id)
            routeName = colander.SchemaNode(colander.String(),
                                            widget=widget.TextInputWidget(),
                                            title="Name your route")
            startRegion = colander.SchemaNode(colander.String(),
                                              widget=widget.Select2Widget(
                                                  values=choices
                                              ), title="Starting Region")
            startSystem = colander.SchemaNode(colander.String(),
                                              widget=widget.AutocompleteInputWidget(
                                                  values='https://system.api.fuelrats.com/typeahead', min_length=3
                                              ), title="Starting system", id='startingsystem')
            waypoints = WaypointSequence(title='Waypoints')
            endRegion = colander.SchemaNode(colander.String(),
                                            widget=widget.Select2Widget(
                                                values=choices
                                            ), title="Ending Region")
            endSystem = colander.SchemaNode(colander.String(),
                                            widget=widget.AutocompleteInputWidget(
                                                values='https://system.api.fuelrats.com/typeahead', min_length=3
                                            ), title="Destination System", id='destinationsystem')
            description = colander.SchemaNode(colander.String(),
                                              widget=widget.TextInputWidget(), title='Route description',
                                              missing=colander.drop)

        schema = RouteSchema()
        routeschema = ScheduleSchema()
        newrouteform = Form(schema, buttons=('submit',), formid='routeform')
        scheduleform = Form(routeschema, buttons=('submit',), formid='scheduleform')
        if request.POST:
            print(request.POST)
            if request.POST['__formid__'] == 'scheduleform':
                print("Got a schedule form submit.")
                print(request.POST)
                try:
                    appstruct = scheduleform.validate(request.POST.items())
                    print(f"Schedule appstruct: {appstruct}")
                    hooks = webhooks.get_webhooks(request, mycarrier.id)
                    if hooks:
                        for hook in hooks:
                            log.debug(f"Process hook {hook['webhook_url']} type {hook['webhook_type']}")
                            if hook['webhook_type'] == 'discord':
                                webhooks.announce_route_scheduled(request, mycarrier.id, appstruct['selectroute'], hook['webhook_url'])

                except ValidationFailure as e:
                    print(f"Validation failed! {e}")
            if request.POST['__formid__'] == 'routeform':
                print("Got a new route submit")
                try:
                    appstruct = newrouteform.validate(request.POST.items())
                    print(appstruct)
                    waypoints = []
                    for wp in appstruct['waypoints']:
                        waypoints.append({'system': wp['system'], 'duration': str(wp['duration'])})
                    newroute = Route(route_name=appstruct['routeName'], start_region=appstruct['startRegion'],
                                     startPoint=appstruct['startSystem'], waypoints=json.dumps(waypoints),
                                     endPoint=appstruct['endSystem'], end_region=appstruct['endRegion'],
                                     description=appstruct['description'], carrier_id=mycarrier.id)
                    request.dbsession.add(newroute)
                    modal_data = {'load_fire': {'icon': 'success', 'message': 'Route added!'}}
                except ValidationFailure as e:
                    log.debug(f"Route form submission validation failed. {e}")

        data = {}
        if modal_data:
            data['modal'] = modal_data
        data['apiKey'] = request.user.apiKey
        data['sidebar'] = menu.populate_sidebar(request)
        data['subview'] = 'routes'
        data['current_view'] = 'routes'
        data['routes'] = populate_routes(request, mycarrier.id)
        print(data['routes'])
        data['formadvanced'] = True
        data['deform'] = True
        data['newrouteform'] = newrouteform.render()
        data['scheduleform'] = scheduleform.render()
        return data


@view_config(route_name='my_carrier', renderer='../templates/my_carrier.jinja2')
def mycarrier_view(request):
    modal_data = None
    if request.POST:
        if 'eventtype' in request.POST:
            # Got a calendar event.
            starttime = datetime.fromisoformat(request.POST['starttime'])
            if 'endtime' in request.POST and request.POST['endtime'] != '':
                endtime = datetime.fromisoformat(request.POST['endtime'])
            else:
                endtime = starttime
            print(request.POST)
            if 'allday' in request.POST:
                allday = True if 'allday' == 'on' else False
            else:
                allday = False
            if request.POST['eventtype'] == 'scheduled_jump':
                newevent = Calendar(carrier_id=request.POST['cid'], owner_id=request.POST['owner_id'],
                                    title=request.POST['title'], start=starttime, end=endtime,
                                    allday=allday, fgcolor="#00AA00", bgcolor="#00FF00",
                                    departureSystem=request.POST['departureSystem'],
                                    arrivalSystem=request.POST['arrivalSystem'])
            else:
                newevent = Calendar(carrier_id=request.POST['cid'], owner_id=request.POST['owner_id'],
                                    title=request.POST['title'], start=starttime, end=endtime,
                                    allday=allday, fgcolor="#00AA00", bgcolor="#00FF00")
            request.dbsession.add(newevent)
            mycarrier = request.dbsession.query(carrier.Carrier).filter(
                carrier.Carrier.owner == request.user.id).one_or_none()
            hooks = webhooks.get_webhooks(request, mycarrier.id)
            request.dbsession.flush()
            request.dbsession.refresh(newevent)
            modal_data = {'load_fire': {'icon': 'success', 'message': 'Calendar event added!'}}
            if hooks:
                for hook in hooks:
                    log.debug(f"Process hook {hook['webhook_url']} type {hook['webhook_type']}")
                    if hook['webhook_type'] == 'discord':
                        print(f"Discord hook, and calendarEvents {hook['calendarEvents']}")
                        if request.POST['eventtype'] == 'scheduled_jump' and hook['calendarEvents']:
                            res = webhooks.schedule_jump(request, newevent.id, hook['webhook_url'])
                            log.debug(f"Hook result: {res}")
                        else:
                            if hook['calendarEvents']:
                                webhooks.calendar_event(request, newevent.id, hook['webhook_url'])

    userdata = usr.populate_user(request)
    if request.user:
        # Debugging backdoor to other CMDRs my_carrier view.
        try:
            if request.user.userlevel > 4 and 'emulate' in request.params:
                mycarrier = request.dbsession.query(carrier.Carrier). \
                    filter(carrier.Carrier.callsign == request.params['emulate']).one_or_none()
            else:
                mycarrier = request.dbsession.query(carrier.Carrier).filter(
                    carrier.Carrier.owner == request.user.id).one_or_none()
        except AttributeError:
            return exc.HTTPFound("/login")
        if not mycarrier:
            # if user.no_carrier:
            #    return {'user': userdata, 'nocarrier': True}
            # log.warning(f"Attempt to access nonexistant own carrier by {user.username}")
            request.user.no_carrier = True
            return {'user': userdata, 'error': 'no carrier!', 'sidebar': menu.populate_sidebar(request)}
        last = mycarrier.lastUpdated
        # log.debug(f"Last update for carrier {cid}: {last}")
        if not last:
            last = datetime.now() - timedelta(minutes=20)  # Cheap hack to sort out missing lastUpdated.
        if last < datetime.now() - timedelta(minutes=15):
            log.debug(f"Refreshing data for {mycarrier.callsign}")
            jcarrier = carrier_data.update_carrier(request, mycarrier.id, request.user)
            if not jcarrier:
                log.warning(f"Carrier update failed for CID {mycarrier.callsign}. Presenting old data.")
        if not request.user.apiKey:
            request.user.apiKey = hexlify(os.urandom(64)).decode()
        finances = carrier_data.get_finances(request, mycarrier.id)
        data = carrier_data.populate_view(request, mycarrier.id, request.user)
        events = carrier_data.populate_calendar(request, mycarrier.id)
        crew = carrier_data.get_crew(request, mycarrier.id)
        cargo = carrier_data.get_cargo(request, mycarrier.id)
        market = carrier_data.get_market(request, mycarrier.id)
        if modal_data:
            data['modal'] = modal_data

        data['view'] = 'My Carrier'
        data['finance'] = finances
        data['calendar'] = True
        data['formadvanced'] = True
        data['events'] = events
        data['crew'] = crew
        data['cargo'] = cargo
        data['apiKey'] = request.user.apiKey
        data['sidebar'] = menu.populate_sidebar(request)
        data['funding_time'] = format_timespan(int(int(mycarrier.balance) /
                                                   int(int(mycarrier.servicesCost) + int(mycarrier.coreCost)) * 604800)) \
            if int(
            mycarrier.balance) > 0 else f'DEBT DECOMMISSION IN {format_timespan(int(300000000 / int(mycarrier.servicesCost + mycarrier.coreCost) * 604800))}'
        return data
    raise exc.HTTPFound(request.route_url('login'))
