import requests
from django.http import JsonResponse
from mdrtb.settings import BASE_URL
import restapi_utils as ru

def getConceptsByType(req, type):
    url = BASE_URL + f'commonlab/concept?type={type}&lang=en'
    concepts = []
    headers = getAuthHeaders(req)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        for concept in response.json()['results']:
            concepts.append({'name': concept['name'], 'uuid': concept['uuid']})
    else:
        print('FROM CONCEPT HELPER')
        print(response.status_code)
        print(response.json()['error']['message'])
    return concepts


def get_attributes_of_labtest(req,uuid):
    status,data = ru.get(req,'commonlab/labtestattributetype',{'testTypeUuid': uuid, 'v': 'full'})
    if status:
        return data['results']
    else:
        return data['message']


def addOrEditTestType(req, data, url):
    headers = getAuthHeaders(req)
    response = requests.post(url, json=data, headers=headers)
    return response


def customAttr(data, dataTypes, removeDT, preferedHandlers, removeHandler):
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
            'name': removeGivenStrFromObjArr(dataTypes, removeDT, 'helpers'),
            'value': data['datatypeClassname']
        },
        'datatypeConfig': '' if data['datatypeConfig'] == None else data['datatypeConfig'],
        'preferredHandlerClassname': {
            'name': removeGivenStrFromObjArr(preferedHandlers, removeHandler, 'helpers'),
            'value': data['preferredHandlerClassname']
        },
        'handlerConfig': '' if data['handlerConfig'] == None else data['handlerConfig']
    }
    return attribute
