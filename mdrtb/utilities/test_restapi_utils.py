import django
import os
import json
from django.test import TestCase, Client, RequestFactory
import utilities.restapi_utils as ru
from unittest import mock
from utilities.common_utils import get_project_root
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.constants import Constants

os.environ['DJANGO_SETTINGS_MODULE'] = 'mdrtb.settings'
django.setup()


class TestRestApiUtil(TestCase):
    test_patient_uuid = None

    def setUp(self):
        self.client = Client()
        self.request = RequestFactory()
        self.TEST_RESOURCES_DIR = f"{get_project_root()}/test_resources/"

    def test_get_concept(self):
        with open(self.TEST_RESOURCES_DIR+'test_get_concepts.json') as concepts_data:
            data = json.load(concepts_data)['results']
            with mock.patch.object(ru, 'get', return_value=(True, data)):
                status, response = ru.get(
                    self.request.request(), 'concept', {})
                self.assertEqual(len(response), len(data))

    def test_get_concept_by_uuid(self):
        with open(self.TEST_RESOURCES_DIR+'test_get_concept_by_uuid.json', encoding='utf-8') as single_json_concept:
            data = json.load(single_json_concept)
            with mock.patch.object(ru, 'get', return_value=(True, data)):
                status, response = ru.get(self.request.request(),
                                          f'concept/{Concepts.BRONCHUS.value}', {})
                self.assertEqual(response['uuid'], data['uuid'])

    def test_create_patient(self):
        patient_data = {
            "identifiers": [
                {
                    "identifier": "202302T01",
                    "identifierType": Constants.DOTS_IDENTIFIER.value,
                    "location": "e77188ff-679a-4547-af3a-dd88bfd1080b"
                }
            ],
            "person": {
                "names": [
                    {
                        "givenName": "Unit",
                        "familyName": "Test Patient"
                    }
                ],
                "gender": "M",
                "addresses": [
                    {
                        "address1": "Test Address",
                        "stateProvince": "82be00a0-894b-42aa-812f-428f23e9fd7a",
                        "country": "Таджикистан"
                    }
                ],
                "age": "20",
                "deathDate": None,
                "dead": False,
                "causeOfDeath": None
            }
        }
        with open(self.TEST_RESOURCES_DIR+'test_create_patient.json', 'r', encoding='utf-8') as new_patient:
            data = json.load(new_patient)
            with mock.patch.object(ru, 'post', return_value=(True, data)):
                status, response = ru.post(
                    self.request.request(), 'patient', patient_data)
                patient_identifier = response['display'].split('-')[0].strip()
                patient_name = patient_data['person']['names'][0]['givenName'] + ' ' + \
                    patient_data['person']['names'][0]['familyName']
                self.assertEqual(patient_identifier,
                                 patient_data['identifiers'][0]['identifier'])
                self.assertEqual(response['person']['display'], patient_name)

    def test_update_person(self):
        person_update = {"gender": "F"}
        with open(self.TEST_RESOURCES_DIR+'test_create_patient.json', 'r', encoding='utf-8') as created_patient:
            gender = json.load(created_patient)['person']['gender']
        with open(self.TEST_RESOURCES_DIR+'test_update_person.json', 'r', encoding='utf-8')as updated_person:
            updated_data = json.load(updated_person)
            updated_gender = updated_data['person']['gender']
            with mock.patch.object(ru, 'post', return_value=(True, updated_data)):
                status, resposne = ru.post(
                    self.request.request(), f'post/{updated_data["uuid"]}', person_update)
                self.assertEqual(person_update['gender'], updated_gender)

    def test_delete_patient(self):
        with mock.patch.object(ru, 'delete', return_value=(True, {})):
            patient_file = open(self.TEST_RESOURCES_DIR +
                                'test_create_patient.json', 'r', encoding='utf-8')
            patient_uuid = json.load(patient_file)['uuid']
            patient_file.close()
            status, _ = ru.delete(self.request.request(),
                                  f'patient/{patient_uuid}')
            if status:
                with open(self.TEST_RESOURCES_DIR+'test_delete_patient.json', 'r', encoding='utf-8') as deleted_patient:
                    data = json.load(deleted_patient)
                    is_voided = data['voided']
                    identifiers = data['identifiers']
                    self.assertTrue(is_voided)
                    self.assertListEqual(identifiers, [])
