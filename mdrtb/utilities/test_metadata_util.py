import unittest
import metadata_util as mu

class TestMetaDataUtil(unittest.TestCase):

    def test_get_message(self):
        value = mu.get_message('mdrtb.tb03.gender.female')
        self.assertEqual('F', value)

    def test_get_message_without_default(self):
        value = mu.get_message('mdrtb.doesnotexist')
        self.assertEqual('mdrtb.doesnotexist', value)

    def test_get_message_with_default(self):
        value = mu.get_message('mdrtb.doesnotexist', default='Does not exist')
        self.assertEqual('Does not exist', value)

    def test_get_message_with_locale(self):
        value = mu.get_message('mdrtb.facility', locale='ru')
        self.assertEqual('Учреждений', value)

    def test_get_message_with_invalid_locale(self):
        try:
            value = mu.get_message('mdrtb.facility', locale='zy')
        except Exception :
            pass
        else:
            self.fail("Cant open the file")
