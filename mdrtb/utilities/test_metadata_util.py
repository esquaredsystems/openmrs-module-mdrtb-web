import unittest
import utilities.metadata_util as mu
from unittest import mock
import utilities.restapi_utils as ru


class TestMetaDataUtil(unittest.TestCase):

    def test_get_message(self):
        value = mu.get_global_msgs('mdrtb.tb03.gender.female')
        self.assertEqual('F', value)

    def test_get_message_without_default(self):
        value = mu.get_global_msgs('mdrtb.doesnotexist')
        self.assertEqual('mdrtb.doesnotexist', value)

    def test_get_message_with_default(self):
        value = mu.get_global_msgs(
            'mdrtb.doesnotexist', default='Does not exist')
        self.assertEqual('Does not exist', value)

    def test_get_message_with_locale(self):
        value = mu.get_global_msgs('mdrtb.facility', locale='ru')
        self.assertEqual('Учреждений', value)

    def test_get_message_with_invalid_locale(self):
        value = mu.get_global_msgs('mdrtb.facility', locale='zy')
        self.assertEqual('mdrtb.facility', value)

    def test_openMRSlib_get_message(self):
        value = mu.get_global_msgs('dictionary.title', source='OpenMRS')
        self.assertEqual('Concept Dictionary Maintenance', value)

    def test_openMRSlib_get_message_without_default(self):
        value = mu.get_global_msgs('mdrtb.doesnotexist', source='OpenMRS')
        self.assertEqual('mdrtb.doesnotexist', value)

    def test_openMRSlib_message_with_default(self):
        value = mu.get_global_msgs(
            'mdrtb.doesnotexist', default='Does not exist', source='OpenMRS')
        self.assertEqual('Does not exist', value)

    def test_openMRSlib_message_with_locale(self):
        value = mu.get_global_msgs(
            'Location.country', locale='ru', source='OpenMRS')
        self.assertEqual('Страна', value)

    def test_openMRSlib_get_message_with_invalid_locale(self):
        value = mu.get_global_msgs(
            'Location.country', locale='zy', source='OpenMRS')
        self.assertEqual('Location.country', value)

    def test_commonlab_get_message(self):
        value = mu.get_global_msgs(
            'commonlabtest.labtestsample.manage', source='commonlab')
        self.assertEqual('Manage Test Samples', value)

    def test_commonlab_get_message_without_default(self):
        value = mu.get_global_msgs('mdrtb.doesnotexist', source='commonlab')
        self.assertEqual('mdrtb.doesnotexist', value)

    def test_commonlab_message_with_default(self):
        value = mu.get_global_msgs(
            'mdrtb.doesnotexist', default='Does not exist', source='commonlab')
        self.assertEqual('Does not exist', value)

    # TODO: get commonlab messages in russian and tjk
    # def test_commonlab_message_with_locale(self):
    #     value = mu.get_message_openMRS_lib('Location.country', locale='ru', source='commonlab')
    #     self.assertEqual('Страна', value)

    def test_commonlab_get_message_with_invalid_locale(self):
        value = mu.get_global_msgs(
            'commonlabtest.labtestsample.manage', locale='zy', source='commonlab')
        self.assertEqual('commonlabtest.labtestsample.manage', value)
