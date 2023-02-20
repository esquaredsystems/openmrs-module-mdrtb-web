from utilities import common_utils as u
from utilities import restapi_utils as ru
from utilities import formsutil as fu
from resources.enums.constants import Constants
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.encounterType import EncounterType


def get_patient(req, uuid):
    patient = {}
    status, patient_data = ru.get(
        req, f'patient/{uuid}', {'v': "full"})
    if status:
        patient['uuid'] = uuid
        patient['name'] = patient_data['person']['display']
        patient['age'] = patient_data['person']['age']
        patient['dob'] = patient_data['person']['birthdate']
        patient['gender'] = patient_data['person']['gender']
        patient['address'] = patient_data['person']['preferredAddress']['display']
        patient['identifiers'] = patient_data['identifiers']
        patient['auditInfo'] = patient_data['auditInfo']
        return patient
    else:
        print('PATIENT NOT FOUND')
        return None


def create_patient(req, data):
    patient_info = {
        "identifiers": [
            {
                "identifier": data['patientidentifier'],
                "identifierType": data['patientidentifiertype'],
                "location": data['district'] if 'facility' not in data else data['facility']

            }
        ],
        "person": {
            "names": [{
                "givenName": data['givenname'],
                "familyName":data['familyname']
            }],

            "gender": data['gender'],
            "addresses": [{
                "address1": data['address'],
                "stateProvince": data['region'],
                "country": data['country'],
            }]
        }}
    if 'dob' in data:
        patient_info['person']['birthdate'] = data['dob']
        patient_info['person']['birthdateEstimated'] = False
    else:
        patient_info['person']['age'] = data['age']

    if 'deceased' in data:
        patient_info['person']['deathDate'] = data['deathdate']
        patient_info['person']['causeOfDeath'] = data['causeofdeath']
    else:
        patient_info['person']['deathDate'] = None
        patient_info['person']['dead'] = False
        patient_info['person']['causeOfDeath'] = None

    if 'voided' in data:
        patient_info['person']['reasonToVoid'] = data['reasontovoid']

    try:
        status, response = ru.post(req, 'patient', patient_info)
        if status:
            return status, response
    except Exception as e:
        raise Exception(str(e))


def enroll_patient_in_program(req, patientid, data):
    try:
        program_body = {
            "patient": patientid,
            "program": data['program'],
            "dateEnrolled": data['enrollmentdate'],
            "location": data.get('facility', data.get('district', None)),
            "dateCompleted": data['completiondate'] if not data['completiondate'] == '' else None,
            "states": [
                {
                    "state": data.get(work_flow_uuid, None),
                    "startDate": data['enrollmentdate'],
                    "endDate": data['completiondate'] if not data['completiondate'] == '' else None
                } for work_flow_uuid in get_programs(req, uuid=data['program'], params={'v': 'custom:(allWorkflows)'}) if data.get(work_flow_uuid)
            ]
        }
        patient_identifier = {
            "identifier": data['identifier'],
            "identifierType": data['identifierType'],
            "location": data.get('facility', data.get('district', None))}

        status, response = ru.post(req, 'programenrollment', program_body)
        identifier_status, _ = ru.post(
            req, f'patient/{patientid}/identifier', patient_identifier)
        if status and identifier_status:
            return response['uuid']
    except Exception as e:
        raise Exception(str(e))


def get_programs(req, uuid=None, params=None):
    if uuid:
        status, response = ru.get(
            req, f'program/{uuid}', params)
        if status:
            return [workFlowUuid['uuid']
                    for workFlowUuid in response['allWorkflows']]
    status, response = ru.get(
        req, 'program', {'v': 'custom:(uuid,name,retired,allWorkflows)'})
    programs = []
    if status:
        for program in response['results']:
            if program['retired'] == False:
                programs.append(program)
        return programs
    else:
        return None


def sort_states(workflowstates, programstates):
    if len(workflowstates) > 0:
        for programstate in programstates:
            state = programstate.get('state')
            if state:
                uuid = state.get('uuid')
                if uuid:
                    concept = next(({'uuid': ws['concept']['uuid'], 'name': ws['concept']['display'].title()}
                                    for ws in workflowstates if ws['uuid'] == uuid), None)
                    if concept:
                        return {
                            "concept": concept,
                            "start_date": programstate.get('startDate')
                        }


def get_program_states(program=None):
    states = [
        {
            "uuid": workflow['concept']['uuid'],
            "concept": workflow['concept']['display'].title(),
            "answer":  sort_states(workflow['states'], program['states']),
        } for workflow in program['program']['allWorkflows'] if not workflow['retired']
    ]
    return states


def get_enrolled_programs_by_patient(req, uuid, enrollment_id=None):
    representation = 'custom:(uuid,program,states,dateEnrolled,dateCompleted,location,outcome)'
    if enrollment_id:
        try:
            status, response = ru.get(
                req, f'programenrollment/{enrollment_id}', {'v': "custom:(uuid,program,states,dateEnrolled,dateCompleted,location,outcome)"})
            if status:
                return {
                    "uuid": response['uuid'],
                    "program": {
                        "uuid": response['program']['uuid'],
                        "name": response['program']['name'],
                    },
                    "dateEnrolled": response['dateEnrolled'],
                    "dateCompleted": response['dateCompleted'],
                    "location": {
                        "uuid": response['location']['uuid'],
                        "name": response['location']['name'],
                    },
                    "outcome": response['outcome'],
                    "states": get_program_states(program=response)

                }
        except Exception as e:
            raise Exception(str(e))

    try:
        status, response = ru.get(req, 'programenrollment', {
                                  'patient': uuid, 'v': representation})
        if status:
            if len(response['results']) <= 0:
                return None
            programs_info = [
                {
                    "uuid": program['uuid'],
                    "program": {
                        "uuid": program['program']['uuid'],
                        "name": program['program']['name'],
                    },
                    "dateEnrolled": program['dateEnrolled'],
                    "dateCompleted": program['dateCompleted'],
                    "location":{
                        "uuid": program['location']['uuid'],
                        "name": program['location']['name'],
                    },
                    "outcome": program['outcome'],
                    "states": get_program_states(program=program)

                } for program in response['results']
            ]
            return programs_info
    except Exception as e:
        raise Exception(str(e))


def get_patient_dashboard_info(req, patientuuid, programuuid, isMdrtb=None):
    # this function will extend to other forms and laborders
    try:
        patient = get_patient(req, patientuuid)
        program = get_enrolled_programs_by_patient(
            req, patientuuid, enrollment_id=programuuid)
        if isMdrtb:
            forms = {
                'tb03us': fu.get_encounters_by_patient_and_type(req, patientuuid, EncounterType.TB03u_MDR.value),
                'aes': fu.get_encounters_by_patient_and_type(req, patientuuid, EncounterType.ADVERSE_EVENT.value),
                'regimens': fu.get_encounters_by_patient_and_type(req, patientuuid, EncounterType.PV_REGIMEN.value)

            }
        else:
            forms = {
                'tb03s': fu.get_encounters_by_patient_and_type(req, patientuuid, EncounterType.TB03.value),
                'form89s': fu.get_encounters_by_patient_and_type(req, patientuuid, EncounterType.FROM_89.value)
            }
        return patient, program, forms
    except Exception as e:
        raise Exception(str(e))


def get_enrolled_program_by_uuid(req, programid):
    try:
        status, response = ru.get(
            req, f'programenrollment/{programid}', {'v': 'full'})
        if status:
            return response
    except Exception as e:
        raise Exception(str(e))


def get_patient_identifiers(req, patient_uuid):
    identifiers = {}
    try:
        status, response = ru.get(
            req, f'patient/{patient_uuid}/identifier', {'v': 'full'})
        if status:
            for identifier in response['results']:
                if identifier['identifierType']['uuid'] == Constants.DOTS_IDENTIFIER.value:

                    identifiers['dots'] = {
                        'type': identifier['identifierType']['uuid'],
                        'identifier': identifier['identifier'],
                        'created_at': identifier['auditInfo']['dateCreated']

                    }
                else:

                    identifiers['mdr'] = {
                        'type': identifier['identifierType']['uuid'], 'identifier': identifier['identifier'], 'created_at': identifier['auditInfo']['dateCreated']}

        return identifiers
    except Exception as e:
        raise Exception(str(e))
