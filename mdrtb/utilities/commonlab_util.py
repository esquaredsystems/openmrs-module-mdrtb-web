import requests
from django.http import JsonResponse
from mdrtb.settings import BASE_URL
from . import restapi_utils as ru
from . import common_utils as u


def get_commonlab_concepts_by_type(req, type):
    status, response = ru.get(req, 'commonlab/concept',
                              {'type': type, 'lang': req.session['locale']})
    concepts = []
    if status:
        for concept in response['results']:
            concepts.append({'name': concept['name'], 'uuid': concept['uuid']})
    else:
        print(response)
    return concepts


def get_commonlab_test_groups():
    testGroups = [
        'SEROLOGY',
        'CARDIOLOGY',
        'OPHTHALMOLOGY',
        'BACTERIOLOGY',
        'BIOCHEMISTRY',
        'BLOOD_BANK',
        'CYTOLOGY',
        'HEMATOLOGY',
        'IMMUNOLOGY',
        'MICROBIOLOGY',
        'RADIOLOGY',
        'SONOLOGY',
        'URINALYSIS',
        'OTHER'
    ]
    return testGroups


def get_preffered_handler():
    attributesPrefferedHandler = [
        {
            'value': 'org.openmrs.web.attribute.handler.DateFieldGenDatatypeHandler',
            'name': 'DateFieldGenDatatype'
        },
        {
            'value': 'org.openmrs.web.attribute.handler.LongFreeTextFileUploadHandler',
            'name': 'LongFreeTextFileUpload'
        },
        {
            'value': 'org.openmrs.web.attribute.handler.BooleanFieldGenDatatypeHandler',
            'name': 'BooleanFieldGenDatatype'
        },
        {
            'value': 'org.openmrs.web.attribute.handler.LongFreeTextTextareaHandler',
            'name': 'LongFreeTextTextarea'
        },
    ]
    return attributesPrefferedHandler


def get_attributes_data_types():
    attributesDataTypes = [
        {
            'value': 'org.openmrs.customdatatype.datatype.DateDatatype.name',
            'name': 'Date'
        },
        {
            'value': 'org.openmrs.customdatatype.datatype.BooleanDatatype.name',
            'name': 'Boolean'
        },
        {
            'value': 'org.openmrs.customdatatype.datatype.LongFreeTextDatatype.name',
            'name': 'LongFreeText'
        },
        {
            'value': 'org.openmrs.customdatatype.datatype.FreeTextDatatype.name',
            'name': 'FreeText'
        },
        {
            'value': 'org.openmrs.customdatatype.datatype.RegexValidatedTextDatatype.name',
            'name': 'RegexValidatedText'
        },
        {
            'value': 'org.openmrs.customdatatype.datatype.ConceptDatatype.name',
            'name': 'Concept'
        },
    ]
    return attributesDataTypes


def get_test_types_by_search(req, query):
    status, response = ru.get(req, 'commonlab/labtesttype')
    labtests = []
    if status:
        for labtest in response['results']:
            if labtest['name'].startswith(query) or labtest['name'] == query or labtest['name'].__contains__(query):
                labtests.append(labtest)
    return labtests


def get_attributes_of_labtest(req, uuid):
    status, data = ru.get(req, 'commonlab/labtestattributetype',
                          {'testTypeUuid': uuid, 'v': 'full'})
    if status:
        sortedAttr = sorted(data['results'], key=lambda x: x['sortWeight'])
        return sortedAttr
    else:
        return data['error']['message']


def add_edit_test_type(req, data, url):
    status, response = ru.post(req, url, data)
    if status:
        return status, response
    return status, response


def custom_attribute(data, removeDT, removeHandler):
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
            'name': u.remove_given_str_from_obj_arr(get_attributes_data_types(), removeDT, 'commonlab'),
            'value': data['datatypeClassname']
        },
        'datatypeConfig': '' if data['datatypeConfig'] == None else data['datatypeConfig'],
        'preferredHandlerClassname': {
            'name': u.remove_given_str_from_obj_arr(get_preffered_handler(), removeHandler, 'commonlab'),
            'value': data['preferredHandlerClassname']
        },
        'handlerConfig': '' if data['handlerConfig'] == None else data['handlerConfig']
    }
    return attribute


def get_patient_encounters(req, uuid):
    status, response = ru.get(req, 'encounter', {'patient': uuid})
    if status:
        return response
    else:
        return None


def get_test_groups_and_tests(req):
    status, response = ru.get(req, 'commonlab/labtesttype', {})
    if status:
        test_groups = [test['testGroup'] for test in response['results']]
        lab_tests = response['results']
    return lab_tests, test_groups


def get_sample_units(req):
    uuid = "5f21ab43-ec32-44b2-88e5-bc4ed2b93fba"
    status, response = ru.get(
        req, f'concept/{uuid}', {'v': 'custom:(setMembers)'})
    units = []
    if status:
        for unit in response['setMembers']:
            units.append({
                'uuid': unit['uuid'],
                'name': unit['display'],
            })
    return units

def get_commonlab_labtesttype(req,uuid):
    status, response = ru.get(req, f'commonlab/labtesttype/{uuid}', {'v': 'full'})
    if status:
        return response
    else:
        return None

def get_reference_concept_of_labtesttype(req,labtestid):
    labtest = get_commonlab_labtesttype(req,labtestid)
    return labtest['referenceConcept']['uuid']
