import utilities.restapi_utils as ru
from django.core.cache import cache
import datetime
from django.shortcuts import redirect


def get_locations_and_set_cache(req):
    locations = cache.get('locations')
    if locations:
        return locations

    status, locations = ru.get(req, 'location', {
        'v': 'custom:(uuid,name,parentLocation,childLocations,attributes,retired)',
        'limit': 500
    })

    if not status:
        return None

    non_retired_locations = [
        location for location in locations['results'] if not location['retired']]
    cache.set('locations', non_retired_locations, timeout=86400)
    return non_retired_locations


def assign_districts_and_sub_regions(req):
    locations = get_locations_and_set_cache(req)
    sorted_locs = [{
        'uuid': location['uuid'],
        'name': location['name'],
        'level': "REGION",
        'children': [
            {
                'uuid': child['uuid'],
                'name': child['name'],
                'level': child['attributes'][0]['display'].split(':')[1].strip(),
                "children": []
            }
            for child in location['childLocations']
        ]
    } for location in locations if location['parentLocation'] is None]

    return sorted_locs, locations


def assign_facilities(req):
    locations_with_districts, locations = assign_districts_and_sub_regions(req)
    for region in locations_with_districts:
        for location in locations:
            for district in region['children']:
                if location['uuid'] == district['uuid']:
                    district['children'].append(
                        {
                            'uuid': child['uuid'],
                            'name': child['name'],
                            'level': location['attributes'][0]['display'].split(':')[1].strip()
                        } for child in location['childLocations']
                    )

    return locations
