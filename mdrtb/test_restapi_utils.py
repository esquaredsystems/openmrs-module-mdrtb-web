from pydoc import cli
import django
import os
import json
from django.test import TestCase, Client , RequestFactory
import restapi_utils as ru
from unittest import mock
from util import get_project_root
import uuid




os.environ['DJANGO_SETTINGS_MODULE'] = 'mdrtb.settings'
django.setup()

class TestRestApiUtil(TestCase):

    def setUp(self):
        self.client = Client()
        

        
    def test_get_labtesttypes(self):
        file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'r',encoding='utf-8')
        data = dict(json.load(file))['results']
        with mock.patch.object(ru,'get',return_value=data[0]['referenceConcept']['uuid']):
            self.assertEquals(ru.get(self.client.request,'commonlab/labtesttype/b769ccb9-6299-4da9-8a99-83fa4d502ca4',{'v': 'full'}),'31bf10e0-0370-102d-b0e3-001ec94a0cc1')
        
        
    def test_get_concept_by_uuid(self):
        file = open(f'{get_project_root()}/mdrtb/test_resources/concepts.json' , 'r',encoding='utf-8')
        data = dict(json.load(file))['results']
        fetched_concept  = {}
        for concept in data:
            if concept['uuid'] == '0737cfba-5ae8-4605-bd52-74c26ee4da9e':
                fetched_concept = concept
        with mock.patch.object(ru,'get',return_value=fetched_concept):
            get_call = ru.get(self.client.request,'concept/0737cfba-5ae8-4605-bd52-74c26ee4da9e')
            self.assertEquals(get_call,fetched_concept)


    def test_post_labtesttype(self):
        file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'r+',encoding='utf-8')
        data = dict(json.load(file))['results']
        print(data)
        with mock.patch.object(ru,'post',return_value={"status_code" : 201}):
            data_to_be_posted =         {
            "uuid" : "746ef7e6-0660-4deb-a19f-52d836e98547",
            "name" : "Smear Microscopy",
            "referenceConcept" : {
                "uuid" : "31bf1518-0370-102d-b0e3-001ec94a0cc1",
                "display" : "A TB smear result"
            },
            "shortName" : "SM",
            "description" : "This is smear test",
            "testGroup" : "Blood Bank" ,
            "requiresSpecimen" : True
        }
            new_data = {"results" : []}
            data.append(data_to_be_posted)
            new_data['results'].append(data)
            print(new_data)
            json_data = json.dumps(new_data)
            file.close()
            file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'w',encoding='utf-8')
            file.write(json_data)
            file.close()
            file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'r',encoding='utf-8')
            data = dict(json.load(file))
            post_call = ru.post(self.client.request,'commonlab/labtesttype',data_to_be_posted)
            self.assertEquals(post_call['status_code'],201)
            self.assertEquals(len(data['results']),3)
