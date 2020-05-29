from datetime import datetime

import colander as colander
import deform as deform
from deform import widget
from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier
from ..utils import capi
from ..utils.encryption import pwd_context


class Login(deform.schema.CSRFSchema):

    name = colander.SchemaNode(
        colander.String(),
        title="Username")

    age = colander.SchemaNode(
        colander.String(),
        title="Password",
        widget=widget.PasswordWidget,
        description="Your password")


@view_config(route_name='login', renderer='../templates/login.jinja2')
def login_view(request):
    print(f"Session: {request.session}")
    if 'test' not in request.session:
        request.session['test'] = True
    if 'email' in request.params:
        print(f"Got a submit! {request.params}")
        res = request.dbsession.query(user.User).filter(user.User.username == request.params['email']).one_or_none()
        if res:
            if pwd_context.verify(request.params['pass'], res.password):
                print("Valid password!")
                headers = remember(request, res.id)
                return exc.HTTPFound(location=request.route_url('home'), headers=headers)
            else:
                print("Wrong password!")
        else:
            print("No user!")
    return {'project': 'Fleet Carrier Management System'}


@view_config(route_name='logout', renderer='../templates.login.jinja2')
def logout_view(request):
    headers = forget(request)
    next = request.route_url('home')
    return exc.HTTPFound(location=next, headers=headers)


@view_config(route_name='register', renderer='../templates/register.jinja2')
def register_view(request):
    print(request.params)
    if 'register' in request.params:
        print("I got a form submission!")
        print(request.params)
        if request.params['pass'] != request.params['pass_verify']:
            return {'reg_failure': True, 'message': 'Passwords do not match.'}
        res = request.dbsession.query(user.User).filter(user.User.username == request.params['email']).one_or_none()
        if res:
            return {'reg_failure': True, 'message': 'User exists!'}
        cryptpass = pwd_context.hash(request.params['pass'])
        newuser = user.User(username=request.params['email'], password=cryptpass, userlevel=1, cmdr_name=request.params['cmdr_name'], has_validated=False, public_carrier=True, banned=False)
        request.dbsession.add(newuser)
        return {'reg_success': True, 'project': 'Fleet Carrier Management System'}
    return {'project': 'Fleet Carrier Management System'}


@view_config(route_name='oauth', renderer='../templates/register.jinja2')
def oauth(request):
    url, state = capi.get_auth_url()
    raise exc.HTTPFound(location=url)


@view_config(route_name='oauth_callback', renderer='../templates/register.jinja2')
def oauth_callback(request):
    user = request.user
    if not user:
        return {'project': 'Error: You should be logged in before completing Oauth!'}
    print(request.params)
    print(request.url)
    state = request.params['state']
    token = capi.get_token(request.url, state=state)
    print(token)
    user.token = token
    user.refresh_token = token['refresh_token']
    user.token_expiration = token['expires_at']
    request.dbsession.add(user)
    jcarrier = capi.get_carrier(user)
    print(jcarrier)
    services = jcarrier['market']['services']
    newcarrier = carrier.Carrier(owner=user.id, callsign=jcarrier['name']['callsign'], name=jcarrier['name']['vanityName'],
                                 currentStarSystem=jcarrier['currentStarSystem'], balance=jcarrier['balance'],
                                 fuel=jcarrier['fuel'], state=jcarrier['state'], theme=jcarrier['theme'],
                                 dockingAccess=jcarrier['dockingAccess'], notoriousAccess=jcarrier['notoriousAccess'],
                                 totalDistanceJumped=jcarrier['itinerary']['totalDistanceJumpedLY'], currentJump=jcarrier['itinerary']['currentJump'],
                                 taxation=jcarrier['finance']['taxation'], coreCost=jcarrier['finance']['coreCost'], servicesCost=jcarrier['finance']['servicesCost'],
                                 jumpsCost=jcarrier['finance']['jumpsCost'], numJumps=jcarrier['finance']['numJumps'], hasCommodities=True,
                                 hasCarrierFuel=True, hasRearm=True if services['rearm']=='ok' else False,
                                 hasShipyard=True if services['shipyard']=='ok' else False,
                                 hasOutfitting=True if services['outfitting']=='ok' else False,
                                 hasBlackMarket=True if services['blackmarket']=='ok' else False,
                                 hasVoucherRedemption=True if services['voucherredemption']=='ok' else False,
                                 hasExploration=True if services['exploration']=='ok' else False,
                                 lastUpdated=datetime.now())
    request.dbsession.add(newcarrier)
    return {'project': 'Got a callback!'}
