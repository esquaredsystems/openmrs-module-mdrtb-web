from utilities import common_utils as u
from utilities import restapi_utils as ru


def get_patient(req, uuid):
    patient = {}
    status, patient_data = ru.get(
        req, f'patient/{uuid}', {'v': "custom:(identifiers,person)"})
    if status:
        patient['uuid'] = uuid
        patient['name'] = patient_data['person']['display']
        patient['age'] = patient_data['person']['age']
        patient['dob'] = patient_data['person']['birthdate']
        patient['identifier'] = patient_data['identifiers'][0]['identifier']
        return patient
    else:
        print('PATIENT NOT FOUND')
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
                        "concept": display,
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
