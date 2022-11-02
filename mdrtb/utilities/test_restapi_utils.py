import django
import os
import json
from django.test import TestCase, Client , RequestFactory
import restapi_utils as ru
from unittest import mock
from util import get_project_root




os.environ['DJANGO_SETTINGS_MODULE'] = 'mdrtb.settings'
django.setup()

class TestRestApiUtil(TestCase):

    def setUp(self):
        self.client = Client()
        self.labtest_len = 2
        
        

        
    def test_get_labtesttypes(self):
        file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'r',encoding='utf-8')
        data = dict(json.load(file))['results']
        file.close()
        with mock.patch.object(ru,'get',return_value=data):
            self.assertEqual(len(data),self.labtest_len)


    def test_get_concept_by_uuid(self):
        file = open(f'{get_project_root()}/mdrtb/test_resources/concepts.json' , 'r',encoding='utf-8')
        data = dict(json.load(file))['results']
        file.close()
        fetched_concept  = {}
        for concept in data:
            if concept['uuid'] == '0737cfba-5ae8-4605-bd52-74c26ee4da9e':
                fetched_concept = concept
        with mock.patch.object(ru,'get',return_value=fetched_concept):
            get_call = ru.get(self.client.request,'concept/0737cfba-5ae8-4605-bd52-74c26ee4da9e')
            self.assertEqual(get_call,fetched_concept)


    def test_post_labtesttype(self):
        file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'r',encoding='utf-8')
        read_data = dict(json.load(file))['results']
        file.close()
        with mock.patch.object(ru,'post',return_value={"status_code" : 201}):
            data_to_be_posted =   {
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
            post_req = ru.post(self.client.request,'commonlab/labtesttype' , data_to_be_posted)
            file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'w',encoding='utf-8')
            new_labtests = read_data.copy()
            new_labtests.append(data_to_be_posted)
            data_to_write = {'results' : new_labtests}
            file.write(json.dumps(data_to_write))
            file.close()
            self.assertEqual(post_req['status_code'] , 201)
            self.labtest_len = len(data_to_write)
            self.assertGreater(len(read_data),len(data_to_write))
            
            



    def test_delete_labtesttype(self):
        file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'r',encoding='utf-8')
        data = dict(json.load(file))['results']
        file.close()
        with mock.patch.object(ru,'delete',return_value={'status_code' : 204}):
            file = open(f'{get_project_root()}/mdrtb/test_resources/labtesttype.json' , 'w',encoding='utf-8')
            delete_req = ru.delete(self.client.request,'commonlab/labtesttype/746ef7e6-0660-4deb-a19f-52d836e98547')
            self.assertEqual(delete_req['status_code'] , 204)
            new_data = data.copy()
            for labtest in new_data:
                if labtest['uuid'] == "746ef7e6-0660-4deb-a19f-52d836e98547":
                    new_data.remove(new_data[new_data.index(labtest)])
            data_to_write = {'results' : new_data}
            file.write(json.dumps(data_to_write))
            file.close()
            self.assertGreater(len(data),len(new_data))





        
