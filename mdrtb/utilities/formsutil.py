
import utilities.metadata_util as mu


def get_form_concepts(concept_ids, req):
    concept_dict = {}
    for id in concept_ids:
        status, response = mu.get_concept_by_uuid(id, req)
        if status:
            print(id)
            answers = []
            for answer in response['answers']:
                answers.append(
                    {'uuid': answer['uuid'], 'name': answer['display']})
                concept_dict[response['display'].lower().replace(
                    ' ', '')] = answers

    return concept_dict
