# Carrier settings form target
# Also, images!
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config
from pyramid_storage.exceptions import FileNotAllowed
from ..models import Carrier, CarrierExtra


@view_config(route_name='settings', renderer='../templates/mytemplate.jinja2')
def settings_view(request):
    carrier = request.dbsession.query(Carrier).filter(Carrier.owner == request.user.id).one_or_none()
    if carrier:
        if request.POST['myfile'].file:
            try:
                filename = request.storage.save(request.POST['myfile'], folder=f'carrier-{carrier.id}', randomize=True)
                cex = request.dbsession.query(CarrierExtra).filter(CarrierExtra.cid == carrier.id).one_or_none()
                if not cex:
                    nc = CarrierExtra(cid=carrier.id, carrier_image=request.storage.url(filename))
                    request.dbsession.add(nc)
                else:
                    request.storage.delete(cex.carrier_image)
                    cex.carrier_image = request.storage.url(filename)
            except FileNotAllowed:
                request.session.flash('Sorry, this file is not allowed.')
                return HTTPSeeOther(request.route_url('my_carrier'))
    return {}


@view_config(route_name='uploadtest', renderer='../templates/uploadtest.jinja2')
def uploadtest_view(request):
    print("In uploadtest-view")
    return {}
