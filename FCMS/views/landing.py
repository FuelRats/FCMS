import colander
from deform import widget, Form
from pyramid.view import view_config

from ..models import Carrier


class Search(colander.MappingSchema):
    system = colander.SchemaNode(colander.String(),
                                 widget=widget.AutocompleteInputWidget(
                                     values='https://system.api.fuelrats.com/typeahead', min_length=3,
                                 style='width:100%', css_class='textinput numberpi', placeholder='Search by System'))


@view_config(route_name='landing', renderer='../templates/landing.jinja2')
def my_view(request):
    request.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '1728000',
    })

    ct =request.dbsession.query(Carrier).filter(Carrier.trackedOnly==True)
    cr = request.dbsession.query(Carrier).filter(Carrier.trackedOnly==False)
    print(ct.count())
    print(cr.count())
    schema = Search()
    searchform = Form(schema, action='/search/system', buttons=('submit',), method='POST')
    rendered_form = searchform.render()
    return {'searchform': rendered_form,  'deform': True, 'tracked_carriers': ct.count(),
            'registered_carriers': cr.count()}
