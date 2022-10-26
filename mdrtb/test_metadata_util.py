"""
See LICENSE file on project directory
"""

import unittest
import metadata_util as mu

class TestConfigurationUtil(unittest.TestCase):

    def test_get_message(self):
        value = mu.get_message('mdrtb.tb03.gender.female')
        self.assertEquals('F', value)

    def test_get_message_without_default(self):
        value = mu.get_message('mdrtb.doesnotexist')
        self.assertEquals('mdrtb.doesnotexist', value)

    def test_get_message_with_default(self):
        value = mu.get_message('mdrtb.doesnotexist', default='Does not exist')
        self.assertEquals('Does not exist', value)

    def test_get_message_with_locale(self):
        value = mu.get_message('mdrtb.facility', locale='ru')
        self.assertEquals('Учреждений', value)

    def test_get_message_with_invalid_locale(self):
        value = mu.get_message('mdrtb.facility', locale='zy')
        # TODO: complete it
