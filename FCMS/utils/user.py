# User data handler, as well as sidebar menu builder.
import json
from datetime import datetime

from FCMS.utils.capi import capi, get_cmdr
from ..models import User


def populate_user(request):
    """
    Populates the user field for view returns.
    :param request: The request object.
    :return:  A dict of user data to pass into view return.
    """
    userdata = {}
    if request.user:
        userdata = {'cmdr_name': request.user.cmdr_name,
                    'cmdr_image': '/static/dist/img/avatar.png',
                    'link': '/my_carrier',
                    'logged_in': True}
    else:
        userdata = {'cmdr_name': "Not logged in",
                    'cmdr_image': '/static/dist/img/avatar.png',
                    'link': '/login',
                    'logged_in': False}
    return userdata


def update_profile(request):
    if request.user:
        ud = get_cmdr(request.user)
        user = request.dbsession.query(User).filter(User.id == request.user.id).one_or_none()
        user.cachedJson = json.dumps(ud)
        user.lastUpdated = datetime.now()


