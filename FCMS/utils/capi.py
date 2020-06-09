import ast
import json
from urllib.parse import urljoin
import requests
from authlib.integrations.base_client import UnsupportedTokenTypeError
from authlib.integrations.requests_client import OAuth2Session
from pyramid import threadlocal
import logging

log = logging.getLogger(__name__)

settings = threadlocal.get_current_registry().settings
capiURL = settings['capiURL'] or 'https://pts-companion.orerve.net'
authURL = settings['authURL'] or 'https://auth.frontierstore.net'
redirectURL = settings['redirectURL'] or 'https://fleetcarrier.space/oauth/callback'
client_id = settings['client_id']
client_secret = settings['client_secret']
token_endpoint = authURL+'/token'
auth_endpoint = authURL+'/auth'


def update_token(token, ref_token=None, user=None):
    log.info(f"update_token called! User: {user}")
    log.debug(f"Token: {token}")
    client.token = token
    try:
        new_token = client.refresh_token(token_endpoint, ref_token)
        if 'message' in new_token:
            log.warning(f"Authlib refresh token Failed! {new_token}: Retrying with request.")
            data = {'grant_type': 'refresh_token', 'refresh_token': ref_token,
                    'client_id': client_id, }
            r = requests.post(urljoin(authURL, token_endpoint), data=data)
            if r.status_code == requests.codes.ok:
                new_token = r.json()
                log.debug(f"Manual refresh: {new_token}")
                return new_token
            else:
                log.error(f"Couldn't refresh authentication token. {r.status_code}: {r.content}")
        else:
            log.info(f"Authentication token refreshed for {user}")
            return new_token
    except UnsupportedTokenTypeError:
        # Failed, let's do it manually.
        data = {'grant_type': 'refresh_token', 'refresh_token': ref_token,
                'client_id': client_id}
        r = requests.post(urljoin(authURL, token_endpoint), data=data)
        if r.status_code == requests.codes.ok:
            new_token = r.json()
            log.info(f"Unsupported token type from authlib. Manual refresh: {new_token}")
            return new_token


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
    # Do a bloody song and dance, because can't be sure if the token passed with the user is a stored db string,
    # a dict fresh from the initial OAuth request, or an authlib token object...
    if not user:
        return None
    log.debug(f"User is of type {type(user)}")
    if isinstance(user.access_token, str):
        client.token = ast.literal_eval(user.access_token)
        refresh_token = ast.literal_eval(user.access_token)['refresh_token']
    elif isinstance(user.access_token, dict):
        client.token = user.access_token
        refresh_token = None
    else:
        refresh_token = None
    log.debug(f"CAPI Refresh token: {refresh_token}")
    if client.token:
        log.debug(f"AT expiration: {client.token.is_expired()} and {client.token['expires_at']}")
        if client.token.is_expired():
            log.debug(f"Expired access token for {user.cmdr_name}!")
            newtoken = update_token(client.token, ref_token=refresh_token, user=user)
            client.token = newtoken
            user.access_token = str(dict(client.token))
            user.refresh_token = client.token['refresh_token']
            user.token_expiration = client.token['expires_at']
            log.debug(f"Updated token: {newtoken}")

        try:
            res = client.get(urljoin(capiURL, endpoint))
            res.raise_for_status()
            return res.content
        except requests.HTTPError as err:
            if res.status_code == 401:
                log.warning(f"CAPI request for {user.cmdr_name} unauthorized. Attempting to refresh token.")
                newtoken = update_token(client.token, ref_token=refresh_token, user=user)
                log.debug(f"New token for {user.cmdr_name}: {newtoken}")
                client.token = newtoken
                user.access_token = str(dict(client.token))
                user.refresh_token = client.token['refresh_token']
                user.token_expiration = client.token['expires_at']
            log.error(f"Failed to get CAPI resource! {err}")
            return None
    else:
        log.error(f"No CAPI token for user {user.cmdr_name}. Bailing.")
        return None


def get_carrier(user):
    """
    Fetches carrier information for a player from CAPI. Needs the user's access token.
    :param user: The user owning the carrier we're fetching.
    :return: A dict with carrier information.
    """
    try:
        return json.loads(capi('/fleetcarrier', user))
    except TypeError:
        log.error(f"CAPI: User {user} - failed to fetch /fleetcarrier endpoint.")
        return None


def get_cmdr(user):
    """
    Fetches commander  information from FDev. Needs the user's access token.
    :param user: The user object for whom we're fetching data
    :return: A dict with player information.
    """
    try:
        return json.loads(capi('/profile', user))
    except TypeError:
        log.error(f"CAPI: User {user} - failed to fetch /profile endpoint.")
        return None


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
