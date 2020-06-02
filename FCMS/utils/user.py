# User data handler, as well as sidebar menu builder.


def populate_user(request):
    """
    Populates the user field for view returns.
    :param request: The request object.
    :return:  A dict of user data to pass into view return.
    """
    userdata = {}
    if request.user:
        userdata = {'cmdr_name': request.user.cmdr_name,
                    'cmdr_image': '/static/dist/img/avatar.png'}
    else:
        userdata = {'cmdr_name': "Not logged in",
                    'cmdr_image': '/static/dist/img/avatar.png'}
    return userdata