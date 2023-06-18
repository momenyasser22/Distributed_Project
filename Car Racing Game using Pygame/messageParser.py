import json

def serializeJSON(message):
    bytes_obj = json.dumps(message).encode('utf-8')
    return bytes_obj


def deserializeJSON(bytes_obj):
    json_obj = json.loads(bytes_obj.decode('utf-8'))
    return json_obj

