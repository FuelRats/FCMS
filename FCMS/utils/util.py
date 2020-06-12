import codecs
from sqlalchemy import inspect


def from_hex(mystr):
    print(mystr)
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
