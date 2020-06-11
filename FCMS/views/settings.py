# Carrier settings form target
# Also, images!
from datetime import datetime

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config
from pyramid_storage.exceptions import FileNotAllowed
from ..models import Carrier, CarrierExtra, Calendar


@view_config(route_name='settings', renderer='../templates/mytemplate.jinja2')
def settings_view(request):
    if request.POST:
        print(f"Got a post. {request.POST.__dict__}")
        starttime = datetime.fromisoformat(request.POST['starttime'])
        endtime = datetime.fromisoformat(request.POST['endtime'])

        if 'allday' in request.POST:
            allday=True if 'allday'=='on' else False
        else:
            allday=False
        newevent = Calendar(carrier_id=1, owner_id=1, title=request.POST['title'], start=starttime,
                            end=endtime,
                            allday=allday,
                            fgcolor="#00AA00", bgcolor="#00FF00")
        request.dbsession.add(newevent)
    return {}


@view_config(route_name='uploadtest', renderer='../templates/uploadtest.jinja2')
def uploadtest_view(request):
    print("In uploadtest-view")
    return {}
