import requests
from django.http import JsonResponse
from mdrtb.settings import BASE_URL
from . import restapi_utils as ru
from . import common_utils as u
 
def get_commonlab_concepts_by_type(req, type):
    status,response = ru.get(req,'commonlab/concept',{'type' :type})
    concepts = []
    if status:
        for concept in response['results']:
                concepts.append({'name': concept['name'], 'uuid': concept['uuid']})
    else:
        print(response)
    return concepts


def get_test_types_by_search(req,query):
    status,response = ru.get(req,'commonlab/labtesttype',{'v' : 'full'})
    labtests = []
    if status:
        for labtest in response['results']:
            if labtest['name'].startswith(query) or labtest['name'] == query or labtest['name'].__contains__(query):
                labtests.append(labtest)
    print(labtests)
    return labtests

def get_attributes_of_labtest(req,uuid):
    status,data = ru.get(req,'commonlab/labtestattributetype',{'testTypeUuid': uuid, 'v': 'full'})
    if status:
        return data['results']
    else:
        return data['error']['message']


def add_edit_test_type(req, data, url):
    status,response = ru.post(req,url,data)
    if status:
        return status, response
    return status, response


def custom_attribute(data, dataTypes, removeDT, preferedHandlers, removeHandler):
    attribute = {
        'uuid': data['uuid'],
        'name': data['name'],
        'description': data['description'],
        'multisetName': '' if data['multisetName'] == None else data['multisetName'],
        'groupName': '' if data['groupName'] == None else data['groupName'],
        'maxOccurs': data['maxOccurs'],
        'minOccurs': data['minOccurs'],
        'sortWeight': data['sortWeight'],
        'datatypeClassname': {
            'name': u.remove_given_str_from_obj_arr(dataTypes, removeDT, 'helpers'),
            'value': data['datatypeClassname']
        },
        'datatypeConfig': '' if data['datatypeConfig'] == None else data['datatypeConfig'],
        'preferredHandlerClassname': {
            'name': u.remove_given_str_from_obj_arr(preferedHandlers, removeHandler, 'helpers'),
            'value': data['preferredHandlerClassname']
        },
        'handlerConfig': '' if data['handlerConfig'] == None else data['handlerConfig']
    }
    return attribute
