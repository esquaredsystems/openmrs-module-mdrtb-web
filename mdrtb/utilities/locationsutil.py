import utilities.restapi_utils as ru
from django.core.cache import cache
import datetime
from django.shortcuts import redirect


def get_locations(req):
    print('MAKING REST CALL')
    status, locations = ru.get(req, 'location', {
        'v': 'custom:(uuid,name,parentLocation,childLocations,attributes,retired)',
        'limit': 500
    })

    if not status:
        return None

    non_retired_locations = [
        location for location in locations['results'] if not location['retired']]
    return non_retired_locations


def get_location_level(uuid, location_by_uuids):
    location = location_by_uuids.get(uuid, {})
    attributes = location.get('attributes', [])
    for attribute in attributes:
        if attribute['attributeType']['uuid'] == "6b738ed1-78b3-4cdb-81f6-7fdc5da20a3d":
            display = attribute.get('display')
            level = display.split(':')[1].strip()
            return level
    return None


def create_location_hierarchy(req):
    locations = cache.get('locations')
    if locations:
        return locations
    locations = get_locations(req)
    location_by_uuids = {location['uuid']: location for location in locations}
    location_hierarchy = []

    for location in locations:
        if location.get('parentLocation') is None and not location.get('retired', True):
            location_hierarchy.append({
                'uuid': location['uuid'],
                'name': location['name'],
                'level': get_location_level(location['uuid'], location_by_uuids),
                'children': [
                    {
                        'uuid': child['uuid'],
                        'name': child['name'],
                        'level': get_location_level(child['uuid'], location_by_uuids),
                        'children': [
                            {
                                'uuid': subchild['uuid'],
                                'name': subchild.get('name', subchild['display']),
                                'level': get_location_level(subchild['uuid'], location_by_uuids),
                            } for subchild in child.get('childLocations', []) if not subchild.get('retired', location_by_uuids.get(subchild['uuid'], {'retired': True})['retired'])
                        ] if child.get('childLocations') else []
                    } for child in location.get('childLocations', []) if not child.get('retired', location_by_uuids.get(child['uuid'], {'retired': True})['retired'])
                ] if location.get('childLocations') else []
            })
    cache.set('locations', location_hierarchy, timeout=86400)
    return location_hierarchy
