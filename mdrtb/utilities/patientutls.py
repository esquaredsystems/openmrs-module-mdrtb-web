from utilities import common_utils as u
from utilities import restapi_utils as ru


def get_patient(req,uuid):
    patient = {}
    status,patient_data = ru.get(req,f'patient/{uuid}',{'v' : "custom:(identifiers,person)"})
    if status:
        patient['uuid'] = uuid
        patient['name'] = patient_data['person']['display']
        patient['age']=patient_data['person']['age']
        patient['dob']=patient_data['person']['birthdate']
        patient['identifier'] = patient_data['identifiers'][0]['identifier']
        return patient
    else:
        print('PATIENT NOT FOUND')
        return None


def get_enrolled_programs_by_patient(req,uuid):
    status,response = ru.get(req,'programenrollment',{'patient':uuid,'v':'full'}) 
    if status:
        return response
    else:
        raise Exception('Error fetching program try again')