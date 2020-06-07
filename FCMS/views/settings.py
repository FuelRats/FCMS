# Carrier settings form target
# Also, images!
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config
from pyramid_storage.exceptions import FileNotAllowed


@view_config(route_name='settings', renderer='../templates/mytemplate.jinja2')
def settings_view(request):
    cid = 1
    if request.POST['myfile'].file:
        try:
            request.storage.save(request.POST['myfile'], folder=f'carrier-{cid}', randomize=True)
        except FileNotAllowed:
            request.session.flash('Sorry, this file is not allowed.')
            return HTTPSeeOther(request.route_url('home'))
    return {}


@view_config(route_name='uploadtest', renderer='../templates/uploadtest.jinja2')
def uploadtest_view(request):
    print("In uploadtest-view")
    return {}
