from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config
from pyramid_storage.exceptions import FileNotAllowed
from ..models import Carrier, CarrierExtra


@view_config(route_name='terms', renderer='../templates/transition.jinja2')
def terms_view(request):
    terms = """
    <p>
    Fleetcarrier.space is provided as a service to Elite: Dangerous players for the purpose of managing
    and displaying their Fleet Carrier for other users, and may not be used for any other purposes,
    be they for profit or not.</p>
    <p>
    To use the majority of the service's functions, users need to be logged in and authenticated against
    Frontier's Commander API. By using this service, you agree that we may store details needed to identify
    you and authenticate you against that API, including but not limited to OAuth2 access tokens, 
    your email address, and details about your Fleet Carrier and your Commander. All such data is stored
    securely in our database.</p>
    <p>
    The service allows you to upload content for your carrier page. This content must not be
    copyrighted work, lewd or obscene in nature, illegal or otherwise unsuitable for public viewing.
    The content must not attempt to circumvent site security or otherwise damage the service, viewers
    of the service, or otherwise be malicious in nature.</p>
    <p>
    As per GDPR laws, you may request a copy of any information this service stores about you, or the
    deletion of said data, by sending an email to gdpr@fuelrats.com.</p>   
    """

    return {'title': 'Fleetcarrier.space Terms of Service', 'message': terms}