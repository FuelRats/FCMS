import colander as colander
import deform as deform
from deform import widget
from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc

from .. import models
from ..utils import capi


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

    return {'project': 'Fleet Carrier Management System'}


@view_config(route_name='register', renderer='../templates/register.jinja2')
def register_view(request):
    print(request.params)
    if 'register' in request.params:
        print("I got a form submission!")
        return {'reg_success': True, 'project': 'Fleet Carrier Management System'}
    return {'project': 'Fleet Carrier Management System'}


@view_config(route_name='oauth', renderer='../templates/register.jinja2')
def oauth(request):
    url, state = capi.get_auth_url()
    raise exc.HTTPFound(location=url)


@view_config(route_name='oauth_callback', renderer='../templates/register.jinja2')
def oauth_callback(request):
    print(request.params)
    print(request.url)
    state = request.params['state']
    print(capi.get_token(request.url, state=state))
    return {'project': 'Got a callback!'}
