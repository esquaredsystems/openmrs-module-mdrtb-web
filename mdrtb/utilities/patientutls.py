from utilities import common_utils as u
from utilities import restapi_utils as ru
from utilities import formsutil as fu


def get_patient(req, uuid):
    patient = {}
    status, patient_data = ru.get(
        req, f'patient/{uuid}', {'v': "custom:(identifiers,person)"})
    if status:
        patient['uuid'] = uuid
        patient['name'] = patient_data['person']['display']
        patient['age'] = patient_data['person']['age']
        patient['dob'] = patient_data['person']['birthdate']
        patient['gender'] = patient_data['person']['gender']
        patient['address'] = patient_data['person']['preferredAddress']['display']
        patient['identifier'] = patient_data['identifiers'][0]['identifier']
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


def get_states(workflowstates, programstates):
    for programstate in programstates:
        state = programstate.get('state')
        if state:
            uuid = state.get('uuid')
            if uuid:
                display = next((ws['concept']['display']
                               for ws in workflowstates if ws['uuid'] == uuid), None)
                if display:
                    return {
                        "concept": display.title(),
                        "start_date": programstate.get('startDate')
                    }


def get_enrolled_programs_by_patient(req, uuid):
    status, response = ru.get(req, 'programenrollment', {
                              'patient': uuid, 'v': 'custom:(uuid,program,states,dateEnrolled,dateCompleted,location,outcome)'})
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
                "states": [

                    {
                        "concept": workflow['concept']['display'],
                        "answer":  get_states(workflow['states'], program['states']),
                    } for workflow in program['program']['allWorkflows']



                ]

            } for program in response['results']
        ]
        return programs_info
    else:
        return None


def get_patient_dashboard_info(req, patientuuid, programuuid, isMdrtb=None):
    # this function will extend to other forms and laborders
    patient = get_patient(req, patientuuid)
    status, response = ru.get(req, f'programenrollment/{programuuid}', {
        'v': 'custom:(uuid,program,states,dateEnrolled,dateCompleted,location,outcome)'})
    if status:
        program_info = {
            "uuid": response['uuid'],
            "program": {
                'uuid': response['program']['uuid'],
                'name': response['program']['name']
            },
            "location": {
                "uuid": response['location']['uuid'],
                "name": response['location']['name'],
            },
            'dateEnrolled': response['dateEnrolled'],
            'dateCompleted': response['dateCompleted'],
            'outcome': response['outcome'],
            "states": [

                {
                    "concept": workflow['concept']['display'].title(),
                    "answer":  get_states(workflow['states'], response['states']),
                } for workflow in response['program']['allWorkflows']



            ]
        }

    if not isMdrtb:
        forms = {'tb03s': fu.get_patient_tb03_forms(req, patientuuid)}
        return patient, program_info, forms
    else:
        return patient, program_info
