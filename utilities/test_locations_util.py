import unittest
from unittest import mock

import utilities.locations_util as lu


def _location(name, *attributes):
    return {
        "name": name,
        "attributes": [
            {"attributeType": {"display": type_name}, "value": value}
            for type_name, value in attributes
        ],
    }


class GetLocationSiteCodesTest(unittest.TestCase):
    """The Site list for sending an order to QuaLIS (Submit Order to Lab)."""

    def _site_codes(self, locations):
        with mock.patch.object(lu, "get_locations", return_value=locations):
            return lu.get_location_site_codes(None)

    def test_only_locations_with_a_site_code_are_listed(self):
        codes = self._site_codes([
            _location("МСШ 4", ("LEVEL", "FACILITY"), ("SITE_CODE", "TJ052")),
            _location("Сино", ("LEVEL", "DISTRICT")),
            _location("No attributes"),
        ])
        self.assertEqual(codes, [{"name": "МСШ 4", "sitecode": "TJ052"}])

    def test_sorted_by_site_code(self):
        codes = self._site_codes([
            _location("B", ("SITE_CODE", "TJ200")),
            _location("A", ("SITE_CODE", "TJ100")),
        ])
        self.assertEqual([c["sitecode"] for c in codes], ["TJ100", "TJ200"])

    def test_none_when_no_location_has_a_site_code(self):
        self.assertEqual(self._site_codes([_location("Сино", ("LEVEL", "DISTRICT"))]), [])

    def test_location_without_attributes_key_is_skipped(self):
        self.assertEqual(self._site_codes([{"name": "Bare"}]), [])
