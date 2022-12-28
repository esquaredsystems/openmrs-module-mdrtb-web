import unittest
import utilities.commonlab_util as cu
import utilities.restapi_utils as ru
import utilities.common_utils as c
from unittest import mock
from django.test import Client
import json


class TestCommonLabUtils(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def test_get_commonlab_concepts_by_type(self):
        file = open(
            f'{c.get_project_root()}/test_resources/labtestconcepts.json', 'r', encoding='utf-8')
        data = dict(json.load(file))['results']
        file.close()
        with mock.patch.object(cu, 'get_commonlab_concepts_by_type', return_value=data):
            actual = len(cu.get_commonlab_concepts_by_type(
                self.client.request, 'commonlab/concepts', {'type': 'labTestType'}))
            expected = len(data)
            self.assertEqual(actual, expected)

    def test_get_test_types_by_search(self):
        file = open(
            f'{c.get_project_root()}/test_resources/labtesttype.json', 'r', encoding='utf-8')
        data = dict(json.load(file))['results']
        file.close()
        with mock.patch.object(cu, 'get_test_types_by_search', return_value=data[1]):
            actual = cu.get_test_types_by_search(
                self.client.request, 'Unknown')
            expected = data[1]
            self.assertEqual(actual, expected)


    def test_get_attributes_of_labtest(self):
        file = open(
            f'{c.get_project_root()}/test_resources/labtestattribute.json', 'r', encoding='utf-8')
        data = dict(json.load(file))['results']
        file.close()
        with mock.patch.object(cu, 'get_attributes_of_labtest', return_value=data):
            actual = cu.get_attributes_of_labtest(self.client.request,'commonlab/labtestattributetype' , {'testTypeUuid' :"aa895125-4750-4b9b-a814-b28344fa575f"})
            expected = data
            self.assertEqual(actual, expected)            

   
        