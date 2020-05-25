import colander as colander
import deform as deform
from deform import widget
from pyramid.view import view_config
from pyramid.response import Response

from .. import models


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
def my_view(request):

    return {'project': 'Fleet Carrier Management System'}
