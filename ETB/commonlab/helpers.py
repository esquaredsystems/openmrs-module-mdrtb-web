import requests
from django.http import JsonResponse

BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1/'


def getAuthHeaders(req):
    headers = {'Authorization': f'Basic {req.session["encodedCredentials"]}',
               'Cookie': f"JSESSIONID={req.session['sessionId']}"}
    return headers


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


def getAttributesByLabTest(uuid):
    url = BASE_URL + 'commonlab/labtestattributetype'
    params = {'testTypeUuid': uuid, 'v': 'full'}
    response = requests.get(url=url, params=params)
    return response.json()['results']


def addOrEditTestType(req, data, url):
    headers = getAuthHeaders(req)
    response = requests.post(url, json=data, headers=headers)
    return response


def removeGivenStrFromArr(arr=[], str=''):
    tCopy = arr.copy()
    tCopy.remove(tCopy[tCopy.index(str)])
    return tCopy


def removeGivenStrFromObjArr(arr, str, call):
    temp = arr.copy()
    removedName = ''
    for item in temp:
        if item['value'] == str:
            removedName = item['name']
            temp.remove(temp[temp.index(item)])
    if call == 'helpers':
        return removedName
    else:
        return temp


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
