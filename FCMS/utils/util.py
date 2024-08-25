import base64
import codecs
import smtplib

from sqlalchemy import inspect
from email.mime.text import MIMEText
import logging

log = logging.getLogger(__name__)


def from_hex(mystr):
    #print(mystr)
    try:
        return bytes.fromhex(mystr).decode('utf-8')
    except TypeError:
        return "Unregistered Carrier"
    except ValueError:
        return "Unregistered Carrier"


def to_hex(mystr):
    try:
        return codecs.encode(mystr.encode(), 'hex')
    except:
        return None


def object_as_dict(obj):
    """
    Converts a SQLAlchemy object (a single row) to a dict.
    https://stackoverflow.com/a/37350445/2214933

    :param obj:
    :return:
    """
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def clean_market_data(obj):
    """
    Removes those naughty drones from a market data list
    :param obj: List or dict containing market data
    :return: A copy of the clean list or dict
    """
    if 'commodities' in obj:
        r = []
        for commodity in obj['commodities']:
            if commodity['categoryname'] != 'NonMarketable':
                r.append(commodity)
        return {'commodities': r}

    if type(obj) is list:
        r = []
        for commodity in obj:
            if commodity['categoryname'] != 'NonMarketable':
                r.append(commodity)
        return r


def send_email(target, subject, body):
    """
    Sends an email through GMail to a user.
    :param target: Target email address
    :param subject: Subject line
    :param body: Body of email
    :return: SMTP status
    """
    msg = f"From: FCMS@fuelrats.com\r\nTo: {target}\r\nSubject: {subject}\r\n{body}"
    try:
        server = smtplib.SMTP('smtp-relay.gmail.com', 587)
        print(server.ehlo('fuelrats.com'))
        print(server.starttls())
        log.debug(f"Sending email... {server.sendmail('FCMS@fuelrats.com', target, msg)}")
        server.close()
    except smtplib.SMTPSenderRefused as e:
        print(f"Well, that didn't work... {e}")
