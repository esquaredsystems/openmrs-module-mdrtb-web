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
    concept_names=None,
):
    program = {"uuid": f"prog-{uuid}", "name": name}
    if concept_names is not None:
        program["concept"] = {"uuid": f"concept-{uuid}", "names": concept_names}
    return {
        "uuid": uuid,
        "dateEnrolled": enrolled,
        "dateCompleted": completed,
        "outcome": {"display": outcome} if outcome else None,
        "location": {"display": location} if location else None,
        "program": program,
    }


class TestGetPatientProgramEnrollments(TestCase):
    def setUp(self):
        self.request = RequestFactory()

    def _req(self, locale="en"):
        request = self.request.get("/")
        request.session = {"locale": locale}
        return request

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
                self._req(), "patient-uuid"
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
                self._req(), "patient-uuid"
            )
        self.assertEqual(result[0]["date_completed"], "2023-12-31T00:00:00.000+0500")

    def test_active_enrollment_has_no_completion_date(self):
        data = {"results": [_enrollment("pp-1", "DOTS PROGRAM", "2024-01-02T00:00:00.000+0500")]}
        with mock.patch.object(ru, "get", return_value=(True, data)):
            result = pu.get_patient_program_enrollments(
                self._req(), "patient-uuid"
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
                self._req(), "patient-uuid"
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
                self._req(), "patient-uuid"
            )
        self.assertEqual(
            result[0],
            {
                "uuid": "pp-1",
                "program_name": "DOTS PROGRAM",
                "date_enrolled": "2024-01-02T00:00:00.000+0500",
                "date_completed": None,
                "location": "Душанбе",
                "outcome": "Вылечен",
            },
        )

    def test_program_name_uses_the_concept_name_for_the_active_locale(self):
        enrollment = _enrollment(
            "pp-1",
            "DOTS Program",
            "2024-01-02T00:00:00.000+0500",
            concept_names=[
                {"name": "DOTS Program", "locale": "en"},
                {"name": "Программа DOTS", "locale": "ru"},
            ],
        )
        with mock.patch.object(ru, "get", return_value=(True, {"results": [enrollment]})):
            result = pu.get_patient_program_enrollments(
                self._req(locale="ru"), "patient-uuid"
            )
        self.assertEqual(result[0]["program_name"], "Программа DOTS")

    def test_program_name_falls_back_to_raw_name_without_a_concept_match(self):
        enrollment = _enrollment(
            "pp-1",
            "DOTS Program",
            "2024-01-02T00:00:00.000+0500",
            concept_names=[{"name": "DOTS Program", "locale": "en"}],
        )
        with mock.patch.object(ru, "get", return_value=(True, {"results": [enrollment]})):
            result = pu.get_patient_program_enrollments(
                self._req(locale="tj"), "patient-uuid"
            )
        self.assertEqual(result[0]["program_name"], "DOTS Program")

    def test_tolerates_missing_location_and_outcome(self):
        enrollment = _enrollment(
            "pp-1", "DOTS PROGRAM", "2024-01-02T00:00:00.000+0500", location=None
        )
        with mock.patch.object(ru, "get", return_value=(True, {"results": [enrollment]})):
            result = pu.get_patient_program_enrollments(
                self._req(), "patient-uuid"
            )
        self.assertIsNone(result[0]["location"])
        self.assertIsNone(result[0]["outcome"])

    def test_returns_empty_list_when_patient_has_no_enrollments(self):
        with mock.patch.object(ru, "get", return_value=(True, {"results": []})):
            result = pu.get_patient_program_enrollments(
                self._req(), "patient-uuid"
            )
        self.assertEqual(result, [])

    def test_returns_empty_list_on_failed_response(self):
        with mock.patch.object(ru, "get", return_value=(False, None)):
            result = pu.get_patient_program_enrollments(
                self._req(), "patient-uuid"
            )
        self.assertEqual(result, [])

    def test_returns_empty_list_on_exception(self):
        with mock.patch.object(ru, "get", side_effect=Exception("boom")):
            result = pu.get_patient_program_enrollments(
                self._req(), "patient-uuid"
            )
        self.assertEqual(result, [])
