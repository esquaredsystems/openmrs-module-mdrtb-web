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


def get_enrolled_programs_by_patient(req, uuid):
    status, response = ru.get(req, 'programenrollment', {
                              'patient': uuid, 'v': 'full'})
    programs_info = []
    if status:
        if len(response['results']) > 0:
            patient_info = {
                "uuid": uuid,
                "name": response['results'][0]['patient']['person']['display'],
                "age": response['results'][0]['patient']['person']['age'],
                "dob": response['results'][0]['patient']['person']['birthdate'],
                "identifier": response['results'][0]['patient']['display'].split('-')[0]

            }
            for program in response['results']:
                programs_info.append({
                    "enrollment_uuid": program['uuid'],
                    "program": {
                        "uuid": program['program']['uuid'],
                        "name": program['program']['name'],
                        "work_flow_states": []
                    },
                    "date_enrolled": program['dateEnrolled'],
                    "date_completed": program['dateCompleted'],
                    "outcome": program['outcome'],
                    "location": {
                        'uuid': program['location']['uuid'],
                        "name": program['location']['display']
                    },
                    "creator": {
                        'uuid': program['auditInfo']['creator']['uuid'],
                        "name": program['auditInfo']['creator']['display']
                    },
                    "states": []

                })
                for workFlowState in program['program']['allWorkflows']:
                    for local_program in programs_info:
                        local_program['program']['work_flow_states'].append(
                            {
                                'concept': {
                                    'uuid': workFlowState['concept']['uuid'],
                                    'name': workFlowState['concept']['display'],
                                    'states': [state['uuid'] for state in workFlowState['states']]
                                }
                            }
                        )
                for state in program['states']:
                    for local_program in programs_info:
                        local_program['states'].append(
                            {
                                "uuid": state['state']['uuid'],
                                'concept': {
                                    'uuid': state['state']['concept']['uuid'],
                                    'name': state['state']['concept']['display'],
                                },
                                "start_date": state['startDate']
                            }
                        )
            final_states = []
            for program_info in programs_info:
                for program_state in program_info['states']:
                    for work_flow_state in program_info['program']['work_flow_states']:
                        for state in work_flow_state['concept']['states']:
                            if program_state['uuid'] == state:
                                final_states.append(
                                    {
                                        'concept': work_flow_state['concept']['name'],
                                        'answer': program_state['concept']['name'],
                                        "start_date": program_state['start_date']
                                    }
                                )
                program_info['states'] = final_states
            return patient_info, programs_info
        else:
            patient = get_patient(req, uuid)
            return patient , []
    else:
        return None
