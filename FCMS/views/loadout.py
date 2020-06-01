from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier
from ..utils import capi
from ..utils import util


@view_config(route_name='loadout', renderer='../templates/loadout_calculator.jinja2')
def loadout_view(request):
    return {}
