import codecs


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
