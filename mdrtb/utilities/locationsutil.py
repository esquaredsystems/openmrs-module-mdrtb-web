import utilities.restapi_utils as ru
from django.core.cache import cache


def get_locations_and_set_cache(req):
    locations = cache.get('locations')
    non_retired_locations = []
    if not locations:
        status, locations = ru.get(
            req, 'location', {'v': 'custom:(uuid,name,parentLocation,childLocations,attributes,retired)', 'limit': 500})
        if status:
            print('FROM REST')
            for location in locations['results']:
                if location['retired'] == False:
                    non_retired_locations.append(location)
            cache.set('locations', non_retired_locations)
            return non_retired_locations
        else:
            return None
    else:
        print('FROM CACHE')
        return locations


def assign_districts_and_sub_regions(req):
    locations = get_locations_and_set_cache(req)
    sorted_locs = []
    if locations:
        for location in locations:
            if location['parentLocation'] is None:
                sorted_locs.append({
                    'uuid': location['uuid'],
                    'name': location['name'],
                    'level': "REGION",
                    'children': []
                })
                for sorted_loc in sorted_locs:
                    if location['uuid'] == sorted_loc['uuid']:
                        for child in location['childLocations']:
                            if child['retired'] == False:
                                sorted_loc['children'].append({
                                    'uuid': child['uuid'],
                                    'name': child['name'],
                                    'level': child['attributes'][0]['display'].split(':')[1].strip(),
                                    "children": []
                                })

    return sorted_locs, locations


def assign_facilities(req):
    locations_with_districts, locations = assign_districts_and_sub_regions(req)
    khatlon = locations_with_districts[16]
    for region in locations_with_districts:
        for district in region['children']:
            for location in locations:
                if district['uuid'] == location['uuid']:
                    for child in location['childLocations']:
                        if child['retired'] == False:
                            if child['childLocations']:
                                district['children'].append(
                                    {
                                        'uuid': child['uuid'],
                                        'name': child['name'],
                                        'level': child['attributes'][0]['display'].split(':')[1].strip(),
                                        "children": [{'uuid': subchild['uuid'], 'name': subchild['name']} for subchild in child['childLocations']]
                                    }
                                )
                            else:
                                district['children'].append(
                                    {
                                        'uuid': child['uuid'],
                                        'name': child['name'],
                                        'level': child['attributes'][0]['display'].split(':')[1].strip(),
                                    })

    return locations_with_districts
