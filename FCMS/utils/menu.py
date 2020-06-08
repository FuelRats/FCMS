# Sidebar menu building tools
from ..utils import user as usr
import logging

log = logging.getLogger(__name__)


def populate_sidebar(request):
    """
    Populates the sidebar menu. Hopefully.
    :param request: The request object.
    :param view: The view being served.
    :return: A dict with jinja2 variables for the sidebar menu.
    """
    sidebar = {}
    user = usr.populate_user(request)
    view = request.current_route_path()
    log.debug(f"Splits: {view.split('/')}")
    log.debug(f"Matched view: {view}")
    log.debug(f"User: {user}")
    sidebar_treeview = None
    if 'carrier' in view.split('/'):
        if len(view.split('/')) > 3:
            root, path, cid, subview = view.split('/')
        else:
            root, path, cid = view.split('/')
            subview = 'summary'
        sidebar_treeview = {
            'icon': 'fa-list',
            'title': 'Carrier Information',
            'current_view': subview,
            'menuitems':
                [
                    {'view': 'summary',
                     'name': 'Summary',
                     'linktarget': request.route_url('carrier', cid=cid),
                     'selectedicon': 'fa-globe',
                     'unselected_icon': 'fa-globe',
                     },
                    {'view': 'market',
                     'name': 'Market',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='market'),
                     'selectedicon': 'fa-dollar-sign',
                     'unselected_icon': 'fa-dollar-sign',
                     },
                    {'view': 'itinerary',
                     'name': 'Itinerary',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='itinerary'),
                     'selectedicon': 'fa-route',
                     'unselected_icon': 'fa-route',
                     },
                    {'view': 'outfitting',
                     'name': 'Outfitting',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='outfitting'),
                     'selectedicon': 'fa-truck',
                     'unselected_icon': 'fa-truck',
                     },
                    {'view': 'shipyard',
                     'name': 'Shipyard',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='shipyard'),
                     'selectedicon': 'fa-ship',
                     'unselected_icon': 'fa-ship',
                     },
                ]
        }
    sidebar_menuitems=[
        {
            'name': 'DSSA Carriers',
            'link': '/search?dssa=True',
            'icon': 'inline_svgs/dssa.jinja2'
        },
        {
            'name': 'Nearest Carriers',
            'link': '/search?type=Closest',
            'icon': 'inline_svgs/starsystem.jinja2'
        },
        {
            'name': 'System Search',
            'link': '/search?dssa=True&term=Fuelum',
            'icon': 'inline_svgs/itinerary.jinja2'
        }
    ]
    sidebar = {
        'sidebar_logo_title': 'FCMS',
        'sidebar_treeview': sidebar_treeview,
        'sidebar_menuitems': sidebar_menuitems

               }
    return sidebar
