import json

import requests
from urllib.parse import urljoin

capiURL = 'https://pts-companion.orerve.net'


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


def get_fdev_cmdr(token):
    """
    Fetches commander  information from FDev. Needs the user's access token.
    :param token: The player's CAPI access token.
    :return: A dict with player information.
    """
    return json.loads(capi('/profile', token))
