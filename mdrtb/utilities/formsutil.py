import utilities.metadata_util as mu
import utilities.restapi_utils as ru
from datetime import datetime
from resources.mdrtbConcepts import Concepts


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


def create_tb03(req, patientuuid, data):
    # TB03 encounter type uuid
    encounterType = "0479de9f-e5ea-45d7-b7a8-cda85bc8bc3d"
    current_patient = req.session['current_patient']
    tb03 = {
        "patientProgramUuid": req.session['current_patient_program'],
        "encounter": {
            "patient": patientuuid,
            "encounterType": encounterType,
            "encounterDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "location": req.session['current_location']['uuid'],
            "obs": [
                # Patient Program Id
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.PATIENT_PROGRAM_ID.value

                },
                # Treatment centre for IP
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S '),
                    "concept": Concepts.TREATMENT_CENTER_FOR_IP.value,
                    "value": req.POST.get(Concepts.TREATMENT_CENTER_FOR_IP.value, None)
                },
                # Treatment centre for CP
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.TREATMENT_CENTER_FOR_CP.value,
                    "value": req.POST.get(Concepts.TREATMENT_CENTER_FOR_CP.value, None)
                },
                # Name of IP Facility
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.NAME_OF_IP_FACILITY.value,
                    "value": req.POST.get(Concepts.NAME_OF_IP_FACILITY.value, None)
                },
                # Name of CP Facility
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.NAME_OF_CP_FACILITY.value,
                    "value": req.POST.get(Concepts.NAME_OF_CP_FACILITY.value, None)
                },
                # Patient Category
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.TUBERCULOSIS_PATIENT_CATEGORY.value,
                    "value": req.POST.get(Concepts.TUBERCULOSIS_PATIENT_CATEGORY.value, None)
                },
                # Date of Treatment Start
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.DOTS_TREATMENT_START_DATE.value,
                    "value": req.POST.get(Concepts.DOTS_TREATMENT_START_DATE.value, None)
                },
                # Site of TB disease
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.ANATOMICAL_SITE_OF_TB.value,
                    "value": req.POST.get(Concepts.ANATOMICAL_SITE_OF_TB.value, None)
                },
                # HIV Test Date
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.DATE_OF_HIV_TEST.value,
                    "value": req.POST.get(Concepts.DATE_OF_HIV_TEST.value, None)
                },
                # HIV Status
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.RESULT_OF_HIV_TEST.value,
                    "value": req.POST.get(Concepts.RESULT_OF_HIV_TEST.value, None)
                },
                # ART Start Date
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.DATE_OF_ART_TREATMENT_START.value,
                    "value": req.POST.get(Concepts.DATE_OF_ART_TREATMENT_START.value, None)
                },
                # PCT Start Date
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.DATE_OF_PCT_TREATMENT_START.value,
                    "value": req.POST.get(Concepts.DATE_OF_PCT_TREATMENT_START.value, None)
                },
                # Date of X-ray
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.XRAY_DATE.value,
                    "value": req.POST.get(Concepts.XRAY_DATE.value, None)
                },
                # Resistance Type
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.RESISTANCE_TYPE.value,
                    "value": req.POST.get(Concepts.RESISTANCE_TYPE.value, None)
                },
                # Treatment Outcome
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.TB_TREATMENT_OUTCOME.value,
                    "value": req.POST.get(Concepts.TB_TREATMENT_OUTCOME.value, None)
                },
                # Date of Treatment Outcome
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.TREATMENT_OUTCOME_DATE.value,
                    "value": req.POST.get(Concepts.TREATMENT_OUTCOME_DATE.value, None)
                },
                # Cause of Death
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.CAUSE_OF_DEATH.value,
                    "value": req.POST.get(Concepts.CAUSE_OF_DEATH.value, None)
                },
                # Other Cause of Death
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.OTHER_CAUSE_OF_DEATH.value,
                    "value": req.POST.get(Concepts.OTHER_CAUSE_OF_DEATH.value, None)
                },
                # Date of death
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.DATE_OF_DEATH_AFTER_TREATMENT_OUTCOME.value,
                    "value": req.POST.get(Concepts.DATE_OF_DEATH_AFTER_TREATMENT_OUTCOME.value, None)
                },
                # Clinical Notes
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "concept": Concepts.CLINICIAN_NOTES.value,
                    "value": req.POST.get(Concepts.CLINICIAN_NOTES.value, None)
                },

            ]
        }
    }
    print('====================================')
    print(tb03)
    print('====================================')

    # status, response = ru.post(req, 'mdrtb/tb03', tb03)
    # if status:
    #     return True
    # else:
    #     return False


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
