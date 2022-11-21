import utilities.restapi_utils as ru

def get_ae_form_concepts(req):
    # 741,742,743,713,738,739,719,758,759,760,762,726,696,733
    concept_ids = ["7047f880-b929-42fc-81f7-b9dbba2d1b15","1051a25f-5609-40d1-9801-10c3b6fd74ab","e31fb77b-3623-4c65-ac86-760a2248fc1b","aa9cb2d0-a6d6-4fb7-bb02-9298235128b2"]
    concept_dict = {}
    for id in concept_ids:
        status,response = ru.get(req,f'concept/{id}',{'lang' : 'en' , 'v' : 'full'})
        if status:
            answers = []
            for answer in response['answers']:
                answers.append({'uuid' : answer['uuid'] , 'name' : answer['display']})
            concept_dict[response['display'].lower().replace(' ' , '')] = answers

    return concept_dict