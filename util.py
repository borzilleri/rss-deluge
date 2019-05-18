from datetime import date, datetime
from dateutil import parser

def json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type %s not serializable" % type(obj))

def json_deserialize(pairs):
    """Load with dates"""
    d = {}
    for k, v in pairs:
        if isinstance(v, str):
            try:
                d[k] = parser.parse(v)
            except ValueError:
                d[k] = v
        else:
            d[k] = v
    return d
