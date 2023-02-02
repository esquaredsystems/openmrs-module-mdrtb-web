import utilities.metadata_util as mu
import utilities.restapi_utils as ru


def get_form_concepts(concept_ids, req):
    concept_dict = {}
    for id in concept_ids:
        status, response = mu.get_concept_by_uuid(id, req)
        if status:
            answers = []
            for answer in response['answers']:
                answers.append(
                    {'uuid': answer['uuid'], 'name': answer['display']})
                concept_dict[response['display'].lower().replace(
                    ' ', '')] = answers

    return concept_dict


def get_patient_tb03_forms(req, patientuuid):
    # This full rep will change to custom:(uuid,encounter)
    status, response = ru.get(
        req, 'mdrtb/tb03', {'v': 'full', 'patient': patientuuid})
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
