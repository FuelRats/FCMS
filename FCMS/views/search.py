from pyramid.view import view_config
from pyramid.response import Response
import pyramid.httpexceptions as exc
from pyramid.security import remember, forget
from ..models import user, carrier
from ..utils import capi
from ..utils import util
import re


@view_config(route_name='search', renderer='../templates/mytemplate.jinja2')
def search_view(request):
    term = request.params['term']
    rs = '^[A-Za-z0-9]{3}-[A-Za-z0-9]{3}$'
    r = re.compile(rs)
    if r.search(term):
        print(f"Regex match for {term}, we're looking for a Carrier callsign most likely.")
        res = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.callsign == term).one_or_none()
        if res:
            raise exc.HTTPFound(request.route_url(f'carrier', cid=term))
            return {}
    res = request.dbsession.query(user.User).filter(user.User.cmdr_name == term)
    if res:
        if res.count() == 1:
            # Single CMDR name hit, go to their carrier.
            row = res.one()
            cx = request.dbsession.query(carrier.Carrier).filter(carrier.Carrier.owner == row.id).one_or_none()
            print(request.route_url(f'carrier', cid=cx.callsign))
            raise exc.HTTPFound(request.route_url(f'carrier', cid=cx.callsign))
        elif res.count() > 1:
            print(f"Multiple CMDR name matches, present list. {res.count()}")
            for row in res:
                print(f"Row: {row}")
    else:
        print(f"No match")
    return {}
