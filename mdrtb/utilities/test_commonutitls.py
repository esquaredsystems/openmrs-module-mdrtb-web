import unittest
import utilities.common_utils as cu


class TestCommonUtils(unittest.TestCase):

    def test_get_project_root(self):
        actual = str(cu.get_project_root())
        expected = "D:\Abdul Basit\es\openmrs-module-mdrtb-web\mdrtb"
        self.assertEqual(actual, expected)

    def test_read_properties_file(self):
        actual = cu.read_properties_file(
            f'{cu.get_project_root()}/test_resources/messages.properties', 'r', encoding='utf-8')
        test_key = actual[1].split('=')
        expected = '9009'
        self.assertEqual(test_key[1].strip(), expected)

    def test_read_properties_file_wrong_path(self):
        actual = cu.read_properties_file(
                f'{cu.get_project_root()}/test_resource/messages.properties', 'r', encoding='utf-8')
        self.assertIsNone(actual)
        
    def test_calculate_age(self):
        actual = cu.calculate_age("03/05/2002")
        expected = 20
        self.assertEqual(actual, expected)

    def test_calculate_age_with_wrong_date_format(self):
        actual = cu.calculate_age("03/2002")
        self.assertIsNone(actual)

    def test_iso_to_normal(self):
        actual = cu.iso_to_normal("2002-01-01T00:00:00.000+0000")
        expected = "2002.01.01"
        self.assertEqual(actual, expected)

    def test_iso_to_normal_with_wrong_date_format(self):
        actual = cu.calculate_age("2002-01-01:0000")
        self.assertIsNone(actual)

    def test_remove_given_str_from_arr(self):
        actual = cu.remove_given_str_from_arr(['h', 'e', 'y'], 'h')
        expected = ['e', 'y']
        self.assertEqual(actual, expected)

    def test_remove_given_str_from_arr_with_wrong_str(self):
        actual = cu.remove_given_str_from_arr(['h', 'e', 'y'], '3')
        expected = ['h', 'e', 'y']
        self.assertEqual(actual, expected)

    def test_remove_given_str_from_arr_with_empty_arr(self):
        actual = cu.remove_given_str_from_arr([], 'g')
        expected = []
        self.assertEqual(actual, expected)

    # def test_remove_given_str_from_obj_arr(self):
    #     actual = cu.remove_given_str_from_obj_arr([{"name" : "A","value" : "B"},{"name" : "C","value" : "D"}], "D", 'helpers')
    #     expected = [{"name" : "A","value" : "B"}]
    #     self.assertEqual(actual, expected)