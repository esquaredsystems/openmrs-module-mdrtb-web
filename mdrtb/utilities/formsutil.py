import utilities.metadata_util as mu
import utilities.restapi_utils as ru
from datetime import datetime


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


def create_tb03(req, patientuuid, data):
    # TB03 encounter type uuid
    encounterType = "0479de9f-e5ea-45d7-b7a8-cda85bc8bc3d"
    current_patient = req.session['current_patient']
    tb03 = {
        "encounter": {
            "patient": patientuuid,
            "encounterType": encounterType,
            "encounterDatetime": datetime.now().isoformat(),
            "location": req.session['current_location']['uuid'],
            "obs": [
                # Treatment centre for IP
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "ddf6e09c-f018-4048-a69f-436ff22308b5",
                    "value": req.POST.get('ddf6e09c-f018-4048-a69f-436ff22308b5', None)
                },
                # Treatment centre for CP
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "2cd70c1e-955d-428e-86cd-3efc5ecbcabd",
                    "value": req.POST.get('2cd70c1e-955d-428e-86cd-3efc5ecbcabd', None)
                },
                # Name of IP Facility
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "c34c30ab-ae45-4004-9dc7-926d5d0ed862",
                    "value": req.POST.get('c34c30ab-ae45-4004-9dc7-926d5d0ed862', None)
                },
                # Name of CP Facility
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "b4fb2f5a-2d8a-4bd7-a547-e6699aa6e592",
                    "value": req.POST.get('b4fb2f5a-2d8a-4bd7-a547-e6699aa6e592', None)
                },
                # Regimen Type
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "ebde5ed8-4717-472d-9172-599af069e94d",
                    "value": req.POST.get('ebde5ed8-4717-472d-9172-599af069e94d', None)
                },
                # Date of Treatment Start
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "7b1d2c97-de39-4f98-b896-b6c3e78cba1e",
                    "value": req.POST.get('7b1d2c97-de39-4f98-b896-b6c3e78cba1e', None)
                },
                # Site of TB disease
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "31b4c61c-0370-102d-b0e3-001ec94a0cc1",
                    "value": req.POST.get('31b4c61c-0370-102d-b0e3-001ec94a0cc1', None)
                },
                # HIV Test Date
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "a8f2eacc-2c36-4ddd-b3b8-d80ecfb27bf3",
                    "value": req.POST.get('a8f2eacc-2c36-4ddd-b3b8-d80ecfb27bf3', None)
                },
                # HIV Status
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "31b94ef8-0370-102d-b0e3-001ec94a0cc1",
                    "value": req.POST.get('31b94ef8-0370-102d-b0e3-001ec94a0cc1', None)
                },
                # ART Start Date
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "767fed8f-3e64-4567-a2c6-258444296787",
                    "value": req.POST.get('767fed8f-3e64-4567-a2c6-258444296787', None)
                },
                # PCT Start Date
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "3458f801-1532-4055-b7f5-f3adf90ec7c7",
                    "value": req.POST.get('3458f801-1532-4055-b7f5-f3adf90ec7c7', None)
                },
                # Date of X-ray
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "5539c878-497d-4a77-a173-e709e5b589f2",
                    "value": req.POST.get('5539c878-497d-4a77-a173-e709e5b589f2', None)
                },
                # Resistance Type
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "3f5a6930-5ead-4880-80ce-6ab79f4f6cb1",
                    "value": req.POST.get('3f5a6930-5ead-4880-80ce-6ab79f4f6cb1', None)
                },
                # Treatment Outcome
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "a690e0c4-3371-49b3-9d52-b390fca3dd90",
                    "value": req.POST.get('a690e0c4-3371-49b3-9d52-b390fca3dd90', None)
                },
                # Date of Treatment Outcome
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "5060d5ce-df8e-4090-b09e-62e40a29201a",
                    "value": req.POST.get('5060d5ce-df8e-4090-b09e-62e40a29201a', None)
                },
                # Cause of Death
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "0f7abf6d-e0bb-46ce-aa69-5214b0d2a295",
                    "value": req.POST.get('0f7abf6d-e0bb-46ce-aa69-5214b0d2a295', None)
                },
                # Other Cause of Death
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "bdac7716-d85b-4d12-a589-e04570644c26",
                    "value": req.POST.get('bdac7716-d85b-4d12-a589-e04570644c26', None)
                },
                # Date of death
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "3d2e4053-26d7-4f86-b88a-93011ae1725f",
                    "value": req.POST.get('3d2e4053-26d7-4f86-b88a-93011ae1725f', None)
                },
                # Clinical Notes
                {
                    "person": patientuuid,
                    "obsDatetime": datetime.now().isoformat(),
                    "concept": "31b474e6-0370-102d-b0e3-001ec94a0cc1",
                    "value": req.POST.get('31b474e6-0370-102d-b0e3-001ec94a0cc1', None)
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
