import ast
import json
from urllib.parse import urljoin
import requests
from authlib.integrations.requests_client import OAuth2Session
from pyramid import threadlocal


settings = threadlocal.get_current_registry().settings
capiURL = settings['capiURL'] or 'https://pcompanion.orerve.net'
authURL = settings['authURL'] or 'https://auth.frontierstore.net'
redirectURL = settings['redirectURL'] or 'https://fleetcarrier.space/oauth/callback'
client_id = settings['client_id']
client_secret = settings['client_secret']
token_endpoint = authURL+'/token'
auth_endpoint = authURL+'/auth'

client = OAuth2Session(client_id=client_id, client_secret=client_secret, scope='auth capi',
                       token_endpoint_auth_method='client_secret_post',
                       redirect_uri=redirectURL)


def capi(endpoint, user):
    """
    Fetches data from CAPI.
    :param endpoint: What endpoint to query
    :param user: The user object
    :return: A string containing the response from CAPI
    """
    client.token = ast.literal_eval(user.access_token)
    try:
        res = client.get(urljoin(capiURL, endpoint))
        res.raise_for_status()
        return res.content
    except requests.HTTPError as err:
        print(f"Failed to get CAPI resource! {err}")


def get_carrier(user):
    """
    Fetches carrier information for a player from CAPI. Needs the user's access token.
    :param user: The user owning the carrier we're fetching.
    :return: A dict with carrier information.
    """
    return json.loads(capi('/fleetcarrier', user))


def get_cmdr(user):
    """
    Fetches commander  information from FDev. Needs the user's access token.
    :param user: The user object for whom we're fetching data
    :return: A dict with player information.
    """
    return json.loads(capi('/profile', user))


def get_auth_url():
    uri, state = client.create_authorization_url(auth_endpoint)
    return uri, state


def get_token(authorization_response, state):
    """
    Fetches an authorization token based on a callback code.
    :param state: OAuth2 session state
    :param authorization_response: The auth response string
    :return: The authorization token.
    """
    client.state = state
    token = client.fetch_token(token_endpoint, authorization_response=authorization_response,
                               method='POST')
    return token
