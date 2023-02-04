import enum
from utilities import restapi_utils as ru
import json

privileges_enum = None


def create_privileges_enum(req):
    global privileges_enum
    status, response = ru.get(req, 'privilege', {})
    if status:
        privileges = {}
        for privilege in response['results']:
            privileges[privilege['display'].replace(
                ' ', '_').upper()] = privilege['uuid']
        privileges_enum = enum.Enum('Privileges', privileges)
    else:
        pass


def get_privileges_enum():
    return privileges_enum
