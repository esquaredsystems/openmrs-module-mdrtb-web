import utilities.metadata_util as mu
import utilities.restapi_utils as ru
from datetime import datetime
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.encounterType import EncounterType
import utilities.common_utils as cu


def get_form_concepts(concept_ids, req):
    concept_dict = {}
    for id in concept_ids:
        try:
            response = mu.get_concept(req, id)
            if response:
                answers = []
                for answer in response['answers']:
                    answers.append(
                        {'uuid': answer['uuid'], 'name': answer['display']})
                    concept_dict[response['display'].lower().replace(
                        ' ', '')] = answers

        except Exception as e:
            raise Exception(str(e))
    return concept_dict


def get_patient_tb03_forms(req, patientuuid):
    # This full rep will change to custom:(uuid,encounter)
    status, response = ru.get(
        req, 'mdrtb/tb03', {'v': 'full', 'q': patientuuid})
    if status:
        return response['results']
    else:
        return None


def get_tb03_by_uuid(req, uuid):
    status, response = ru.get(req, f'mdrtb/tb03/{uuid}', {'v': 'full'})
    if status:
        return response
    else:
        return None


def create_update_tb03(req, patientuuid, data, formid=None):
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                tb03 = {
                    "patientProgramUuid": req.session['current_patient_program'],
                    "encounter": {
                        "uuid": response['uuid'],
                        "obs": [
                            # Patient Program Id
                            {
                                "person": patientuuid,
                                "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                                "concept": Concepts.PATIENT_PROGRAM_ID.value
                            }
                        ]



                    }
                }
        except Exception as e:
            raise Exception(str(e))
    else:
        tb03 = {
            "patientProgramUuid": req.session['current_patient_program'],
            "encounter": {
                "patient": patientuuid,
                "encounterType": EncounterType.TB03.value,
                "encounterDatetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "location": req.session['current_location']['uuid'],
                "obs": [
                    # Patient Program Id
                    {
                        "person": patientuuid,
                        "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "concept": Concepts.PATIENT_PROGRAM_ID.value
                    }
                ]



            }
        }
    for key, value in data.items():
        if key == "csrfmiddlewaretoken":
            continue
        if value:
            tb03['encounter']['obs'].append(
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": key,
                    "value": value if not cu.is_date(value) else cu.date_to_sql_format(value)
                }
            )
    try:
        # This returns the newly created TB03 form
        status, _ = ru.post(req, 'mdrtb/tb03', tb03)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def get_tb03_encounters_by_patient(req, patientid):
    try:
        status, response = ru.get(req, 'encounter', {
            'v': 'custom:(uuid,location,encounterDatetime)',
            'encounterType': EncounterType.TB03.value,
            'patient': patientid
        })
        if status:
            return response['results']
    except Exception as e:
        return None


def get_tb03u_encounters_by_patient(req, patientid):
    try:
        status, response = ru.get(req, 'encounter', {
            'v': 'custom:(uuid,location,encounterDatetime)',
            'encounterType': EncounterType.TB03u_MDR.value,
            'patient': patientid
        })
        if status:
            return response['results']
    except Exception as e:
        return None


def remove_duplicate_concepts(concept_field, form_field):
    if form_field:
        for concept in concept_field:
            if form_field['uuid'] == concept['uuid']:
                concept_field.remove(concept)


def remove_tb03_duplicates(concepts, form_data):
    remove_duplicate_concepts(concepts.get(
        'treatmentcenterforip', []), form_data.get('treatmentSiteIP', None))
    remove_duplicate_concepts(concepts.get(
        'treatmentcenterforcp', []), form_data.get('treatmentSiteCP', None))
    remove_duplicate_concepts(concepts.get(
        'causeofdeath', []), form_data.get('causeOfDeath', None))
    remove_duplicate_concepts(concepts.get(
        'resistancetype', []), form_data.get('resistanceType', None))
    remove_duplicate_concepts(concepts.get(
        'resultofhivtest', []), form_data.get('hivStatus', None))
    remove_duplicate_concepts(concepts.get(
        'siteoftbdisease', []), form_data.get('anatomicalSite', None))
    remove_duplicate_concepts(concepts.get(
        'tuberculosispatientcategory', []), form_data.get('patientCategory', None))
    remove_duplicate_concepts(concepts.get(
        'tuberculosistreatmentoutcome', []), form_data.get('treatmentOutcome', None))
