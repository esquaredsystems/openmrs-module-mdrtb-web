import django
import os
from django.test import TestCase, RequestFactory
from unittest import mock
import utilities.patient_utils as pu
import utilities.restapi_utils as ru

os.environ["DJANGO_SETTINGS_MODULE"] = "settings.settings"
django.setup()


def _enrollment(
    uuid,
    name,
    enrolled,
    completed=None,
    location="Вандж (Ванч) (03)",
    outcome=None,
):
    return {
        "uuid": uuid,
        "dateEnrolled": enrolled,
        "dateCompleted": completed,
        "outcome": {"display": outcome} if outcome else None,
        "location": {"display": location} if location else None,
        "program": {"uuid": f"prog-{uuid}", "name": name},
    }


class TestGetPatientProgramEnrollments(TestCase):
    def setUp(self):
        self.request = RequestFactory()

    def test_includes_completed_enrollments(self):
        data = {
            "results": [
                _enrollment("pp-1", "DOTS PROGRAM", "2024-01-02T00:00:00.000+0500"),
                _enrollment(
                    "pp-2",
                    "MDR-TB PROGRAM",
                    "2023-01-01T00:00:00.000+0500",
                    completed="2023-12-31T00:00:00.000+0500",
                ),
            ]
        }
        with mock.patch.object(ru, "get", return_value=(True, data)):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertEqual({p["uuid"] for p in result}, {"pp-1", "pp-2"})

    def test_carries_the_completion_date_through(self):
        data = {
            "results": [
                _enrollment(
                    "pp-2",
                    "MDR-TB PROGRAM",
                    "2023-01-01T00:00:00.000+0500",
                    completed="2023-12-31T00:00:00.000+0500",
                ),
            ]
        }
        with mock.patch.object(ru, "get", return_value=(True, data)):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertEqual(result[0]["date_completed"], "2023-12-31T00:00:00.000+0500")

    def test_active_enrollment_has_no_completion_date(self):
        data = {"results": [_enrollment("pp-1", "DOTS PROGRAM", "2024-01-02T00:00:00.000+0500")]}
        with mock.patch.object(ru, "get", return_value=(True, data)):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertIsNone(result[0]["date_completed"])

    def test_sorts_newest_enrolled_first(self):
        data = {
            "results": [
                _enrollment("pp-old", "DOTS PROGRAM", "2022-05-01T00:00:00.000+0500"),
                _enrollment("pp-new", "MDR-TB PROGRAM", "2024-05-01T00:00:00.000+0500"),
            ]
        }
        with mock.patch.object(ru, "get", return_value=(True, data)):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertEqual([p["uuid"] for p in result], ["pp-new", "pp-old"])

    def test_maps_only_the_picker_fields(self):
        data = {
            "results": [
                _enrollment(
                    "pp-1",
                    "DOTS PROGRAM",
                    "2024-01-02T00:00:00.000+0500",
                    location="Душанбе",
                    outcome="Вылечен",
                )
            ]
        }
        with mock.patch.object(ru, "get", return_value=(True, data)):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertEqual(
            result[0],
            {
                "uuid": "pp-1",
                "program_uuid": "prog-pp-1",
                "program_name": "DOTS PROGRAM",
                "date_enrolled": "2024-01-02T00:00:00.000+0500",
                "date_completed": None,
                "location": "Душанбе",
                "outcome": "Вылечен",
            },
        )

    def test_tolerates_missing_location_and_outcome(self):
        enrollment = _enrollment(
            "pp-1", "DOTS PROGRAM", "2024-01-02T00:00:00.000+0500", location=None
        )
        with mock.patch.object(ru, "get", return_value=(True, {"results": [enrollment]})):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertIsNone(result[0]["location"])
        self.assertIsNone(result[0]["outcome"])

    def test_returns_empty_list_when_patient_has_no_enrollments(self):
        with mock.patch.object(ru, "get", return_value=(True, {"results": []})):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertEqual(result, [])

    def test_returns_empty_list_on_failed_response(self):
        with mock.patch.object(ru, "get", return_value=(False, None)):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertEqual(result, [])

    def test_returns_empty_list_on_exception(self):
        with mock.patch.object(ru, "get", side_effect=Exception("boom")):
            result = pu.get_patient_program_enrollments(
                self.request.request(), "patient-uuid"
            )
        self.assertEqual(result, [])
