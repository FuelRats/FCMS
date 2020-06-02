# Sidebar menu building tools
from ..utils import user as usr


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
    print(f"Splits: {view.split('/')}")
    print(f"Matched view: {view}")
    print(f"User: {user}")
    if 'carrier' in view.split('/'):
        sidebar_treeview = {
            'icon': 'list',
            'title': 'Carrier Information',
        }
    sidebar = {
        'sidebar_logo_title': 'FCMS',
        'sidebar_treeview': sidebar_treeview,

               }
    return sidebar
