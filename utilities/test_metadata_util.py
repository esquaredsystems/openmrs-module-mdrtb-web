import unittest
from unittest import mock

import utilities.messages_util as msg
import utilities.metadata_util as mu

# Translations as they would sit in the Redis cache (message_properties table)
# and in the shipped resources/messages*.properties files. The tests run
# against these instead of whatever the live cache holds, so they no longer
# pass or fail depending on what happens to be cached on the machine.
CACHED = {
    "en": {
        "mdrtb.tb03.gender.female": "F",
        "mdrtb.facility": "Facility",
        "dictionary.title": "Concept Dictionary Maintenance",
        "Location.country": "Country",
        "commonlabtest.labtestsample.manage": "Manage Test Samples",
        "mdrtb.tagged": "Line one<br>Line two",
    },
    "ru": {
        "mdrtb.facility": "Учреждение",
        "Location.country": "Страна",
        # Stored untranslated (same as English); the shipped file has the real text.
        "commonlabtest.labtestsample.manage": "Manage Test Samples",
    },
}
FILES = {
    "en": {"mdrtb.onlyInFile": "Only in the file"},
    "ru": {"commonlabtest.labtestsample.manage": "Управление образцами"},
}


class TestMetaDataUtil(unittest.TestCase):
    """mu.get_global_msgs -> messages_util.lookup, with its fallback order:
    cached language -> cached English -> shipped file -> English file ->
    the default -> the code itself."""

    def setUp(self):
        patches = [
            mock.patch.object(msg, "get_cached", side_effect=lambda lang: CACHED.get(msg.normalise_lang(lang))),
            mock.patch.object(msg, "_file_messages", side_effect=lambda lang: FILES.get(msg.normalise_lang(lang), {})),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_get_message(self):
        self.assertEqual("F", mu.get_global_msgs("mdrtb.tb03.gender.female"))

    def test_get_message_without_default(self):
        self.assertEqual("mdrtb.doesnotexist", mu.get_global_msgs("mdrtb.doesnotexist"))

    def test_get_message_with_default(self):
        value = mu.get_global_msgs("mdrtb.doesnotexist", default="Does not exist")
        self.assertEqual("Does not exist", value)

    def test_get_message_with_locale(self):
        self.assertEqual("Учреждение", mu.get_global_msgs("mdrtb.facility", locale="ru"))

    def test_get_message_with_regional_locale(self):
        self.assertEqual("Учреждение", mu.get_global_msgs("mdrtb.facility", locale="ru_RU"))

    def test_get_message_with_invalid_locale_falls_back_to_english(self):
        self.assertEqual("Facility", mu.get_global_msgs("mdrtb.facility", locale="zy"))

    def test_get_message_missing_in_language_falls_back_to_english(self):
        value = mu.get_global_msgs("mdrtb.tb03.gender.female", locale="ru")
        self.assertEqual("F", value)

    def test_get_message_falls_back_to_shipped_file(self):
        value = mu.get_global_msgs("mdrtb.onlyInFile", locale="ru")
        self.assertEqual("Only in the file", value)

    def test_untranslated_stored_value_prefers_shipped_translation(self):
        value = mu.get_global_msgs("commonlabtest.labtestsample.manage", locale="ru")
        self.assertEqual("Управление образцами", value)

    def test_html_tags_become_spaces(self):
        self.assertEqual("Line one Line two", mu.get_global_msgs("mdrtb.tagged"))

    def test_empty_code_is_rejected(self):
        with self.assertRaises(Exception):
            mu.get_global_msgs("")

    # `source` used to pick the mdrtb / OpenMRS / commonlab property file. All
    # three now live in one table, so it is accepted and ignored.
    def test_openMRSlib_get_message(self):
        value = mu.get_global_msgs("dictionary.title", source="OpenMRS")
        self.assertEqual("Concept Dictionary Maintenance", value)

    def test_openMRSlib_get_message_without_default(self):
        value = mu.get_global_msgs("mdrtb.doesnotexist", source="OpenMRS")
        self.assertEqual("mdrtb.doesnotexist", value)

    def test_openMRSlib_message_with_default(self):
        value = mu.get_global_msgs("mdrtb.doesnotexist", default="Does not exist", source="OpenMRS")
        self.assertEqual("Does not exist", value)

    def test_openMRSlib_message_with_locale(self):
        value = mu.get_global_msgs("Location.country", locale="ru", source="OpenMRS")
        self.assertEqual("Страна", value)

    def test_openMRSlib_get_message_with_invalid_locale_falls_back_to_english(self):
        value = mu.get_global_msgs("Location.country", locale="zy", source="OpenMRS")
        self.assertEqual("Country", value)

    def test_commonlab_get_message(self):
        value = mu.get_global_msgs("commonlabtest.labtestsample.manage", source="commonlab")
        self.assertEqual("Manage Test Samples", value)

    def test_commonlab_get_message_without_default(self):
        value = mu.get_global_msgs("mdrtb.doesnotexist", source="commonlab")
        self.assertEqual("mdrtb.doesnotexist", value)

    def test_commonlab_message_with_default(self):
        value = mu.get_global_msgs("mdrtb.doesnotexist", default="Does not exist", source="commonlab")
        self.assertEqual("Does not exist", value)

    def test_commonlab_get_message_with_invalid_locale_falls_back_to_english(self):
        value = mu.get_global_msgs("commonlabtest.labtestsample.manage", locale="zy", source="commonlab")
        self.assertEqual("Manage Test Samples", value)
