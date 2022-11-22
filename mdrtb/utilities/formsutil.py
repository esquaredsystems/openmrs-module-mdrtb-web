import utilities.metadata_util as mu

def get_form_concepts(concept_ids,req):
    concept_dict={}
    for id in concept_ids:
        try:
            status,response = mu.get_concept_by_uuid(id,req)
            if status: 
                answers = []
                for answer in response['answers']:
                    answers.append({'uuid' : answer['uuid'] , 'name' : answer['display']})
                print(concept_dict[response['display'].lower().replace(' ' , '')])
                concept_dict[response['display'].lower().replace(' ' , '')] = answers
        except Exception as e:
            print(e)
            return None


