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
    if 'my_carrier' in view.split('/') or 'settings' in view.split('/'):
        if len(view.split('/')) > 2:
            root, path, subview = view.split('/')
        else:
            root, path = view.split('/')
            subview = 'summary'
        sidebar_treeview = {
            'icon': 'fa-list',
            'title': 'Carrier Information',
            'current_view': subview,
            'menuitems':
                [
                    {'view': 'summary',
                     'name': 'Summary',
                     'linktarget': request.route_url('my_carrier'),
                     'selected_icon': 'fa-globe',
                     'unselected_icon': 'fa-globe',
                     },
                    {'view': 'market',
                     'name': 'Market',
                     'linktarget': request.route_url('my_carrier_subview', subview='market'),
                     'selected_icon': 'fa-hand-holding-usd',
                     'unselected_icon': 'fa-dollar-sign',
                     },
                    {'view': 'calendar',
                     'name': 'Calendar',
                     'linktarget': request.route_url('my_carrier_subview', subview='calendar'),
                     'selected_icon': 'fa-calendar-alt',
                     'unselected_icon': 'fa-calendar',
                     },
                    {'view': 'messages',
                     'name': 'Messages',
                     'linktarget': request.route_url('my_carrier_subview', subview='messages'),
                     'selected_icon': 'fa-envelope-open',
                     'unselected_icon': 'fa-envelope',
                     },

                    {'view': 'settings',
                     'name': 'Settings',
                     'linktarget': request.route_url('settings'),
                     'selected_icon': 'fa-bars',
                     'unselected_icon': 'fa-bars',
                     },
                    {'view': 'webhooks',
                     'name': 'Webhooks',
                     'linktarget': request.route_url('settings'),
                     'selected_icon': 'fa-code',
                     'unselected_icon': 'fa-code',
                     },
                ]
        }

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
                     'selected_icon': 'fa-globe',
                     'unselected_icon': 'fa-globe',
                     },
                    {'view': 'market',
                     'name': 'Market',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='market'),
                     'selected_icon': 'fa-dollar-sign',
                     'unselected_icon': 'fa-dollar-sign',
                     },
                    {'view': 'itinerary',
                     'name': 'Itinerary',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='itinerary'),
                     'selected_icon': 'fa-route',
                     'unselected_icon': 'fa-route',
                     },
                    {'view': 'outfitting',
                     'name': 'Outfitting',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='outfitting'),
                     'selected_icon': 'fa-truck',
                     'unselected_icon': 'fa-truck',
                     },
                    {'view': 'shipyard',
                     'name': 'Shipyard',
                     'linktarget': request.route_url('carrier_subview', cid=cid, subview='shipyard'),
                     'selected_icon': 'fa-ship',
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
            'link': '/search?searchform=True',
            'icon': 'inline_svgs/itinerary.jinja2'
        }
    ]
    sidebar = {
        'sidebar_logo_title': 'FCMS',
        'sidebar_treeview': sidebar_treeview,
        'sidebar_menuitems': sidebar_menuitems

               }
    return sidebar
