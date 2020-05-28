import json

import requests
from urllib.parse import urljoin
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


def capi(endpoint, token):
    """
    Fetches data from CAPI.
    :param endpoint: What endpoint to query
    :param token: User's access token
    :return: A string containing the response from CAPI
    """

    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(urljoin(capiURL, endpoint), headers=headers)
        r.raise_for_status()
        return r.content
    except requests.HTTPError as err:
        print(f"Nope! {err}")


def get_carrier(token):
    """
    Fetches carrier information for a player from CAPI. Needs the user's access token.
    :param token: The player's CAPI access token.
    :return: A dict with carrier information.
    """
    return json.loads(capi('/fleetcarrier', token))


def get_cmdr(token):
    """
    Fetches commander  information from FDev. Needs the user's access token.
    :param token: The player's CAPI access token.
    :return: A dict with player information.
    """
    return json.loads(capi('/profile', token))


def get_auth_url():
    client = OAuth2Session(client_id=client_id, client_secret=client_secret, scope='auth capi',
                           token_endpoint_auth_method='client_secret_post',
                           redirect_uri=redirectURL)
    uri, state = client.create_authorization_url(auth_endpoint)
    return uri, state


def get_token(authorization_response, state):
    """
    Fetches an authorization token based on a callback code.
    :param state: OAuth2 session state
    :param authorization_response: The auth response string
    :return: The authorization token.
    """
    client = OAuth2Session(client_id=client_id, client_secret=client_secret, state=state,
                           token_endpoint_auth_method='client_secret_post',
                           redirect_uri=redirectURL)
    token = client.fetch_token(token_endpoint, authorization_response=authorization_response,
                               method='POST')
    return token

