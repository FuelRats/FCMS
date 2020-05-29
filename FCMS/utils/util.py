import codecs


def from_hex(mystr):
    print(mystr)
    try:
        return bytes.fromhex(mystr).decode('utf-8')
    except TypeError:
        return "Invalid data"
    except ValueError:
        return "Invalid data"


def to_hex(mystr):
    try:
        return codecs.encode(mystr.encode(), 'hex')
    except:
        return None
