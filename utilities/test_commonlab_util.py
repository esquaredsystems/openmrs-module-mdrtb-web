import django
import os
from django.test import TestCase, RequestFactory
import utilities.commonlab_util as cu

os.environ["DJANGO_SETTINGS_MODULE"] = "settings.settings"
django.setup()


def _full_order(patient_program="__absent__", date_activated="2024-01-01T00:00:00.000+0500"):
    order = {
        "uuid": "order-uuid",
        "labReferenceNumber": "20240101-1",
        "order": {
            "patient": {"uuid": "patient-uuid"},
            "encounter": {"uuid": "enc-uuid", "display": "Specimen Collection"},
            "instructions": None,
            "careSetting": {"uuid": "cs-uuid", "display": "Outpatient"},
            "dateActivated": date_activated,
        },
        "labTestType": {
            "uuid": "ltt-uuid",
            "name": "GeneXpert",
            "testGroup": "BACTERIOLOGY",
        },
    }
    if patient_program != "__absent__":
        order["patientProgram"] = patient_program
    return order


class TestResolveLabOrderProgram(TestCase):
    def setUp(self):
        self.request = RequestFactory()
        self.programs = [
            {"uuid": "pp-1", "program_name": "DOTS PROGRAM"},
            {"uuid": "pp-2", "program_name": "MDR-TB PROGRAM"},
        ]

    def _req(self, session=None):
        request = self.request.get("/")
        request.session = session or {}
        return request

    def test_returns_none_when_no_programs(self):
        self.assertIsNone(cu.resolve_lab_order_program(self._req(), []))

    def test_returns_the_sole_program(self):
        self.assertEqual(
            cu.resolve_lab_order_program(self._req(), [self.programs[0]]), "pp-1"
        )

    def test_returns_the_sole_program_even_if_completed(self):
        completed = {**self.programs[0], "date_completed": "2023-01-01T00:00:00.000+0500"}
        self.assertEqual(cu.resolve_lab_order_program(self._req(), [completed]), "pp-1")

    def test_prefers_the_session_episode_when_present(self):
        request = self._req(
            {"current_patient_program_flow": {"current_program": {"uuid": "pp-2"}}}
        )
        self.assertEqual(cu.resolve_lab_order_program(request, self.programs), "pp-2")

    def test_ignores_a_session_episode_that_is_not_one_of_the_enrollments(self):
        request = self._req(
            {"current_patient_program_flow": {"current_program": {"uuid": "pp-stale"}}}
        )
        self.assertIsNone(cu.resolve_lab_order_program(request, self.programs))

    def test_returns_none_for_several_programs_without_a_hint(self):
        self.assertIsNone(cu.resolve_lab_order_program(self._req(), self.programs))

    def test_tolerates_an_empty_session(self):
        self.assertEqual(
            cu.resolve_lab_order_program(self._req({}), [self.programs[0]]), "pp-1"
        )


class TestLabOrderDateAfterProgramCompletion(TestCase):
    def test_false_when_no_program_selected(self):
        self.assertFalse(cu.lab_order_date_after_program_completion("2024-05-01", None))

    def test_false_when_program_is_still_active(self):
        program = {"uuid": "pp-1", "date_completed": None}
        self.assertFalse(
            cu.lab_order_date_after_program_completion("2024-05-01", program)
        )

    def test_false_when_order_date_is_on_the_completion_date(self):
        program = {"uuid": "pp-1", "date_completed": "2024-05-01T00:00:00.000+0500"}
        self.assertFalse(
            cu.lab_order_date_after_program_completion("2024-05-01", program)
        )

    def test_false_when_order_date_is_before_completion(self):
        program = {"uuid": "pp-1", "date_completed": "2024-05-01T00:00:00.000+0500"}
        self.assertFalse(
            cu.lab_order_date_after_program_completion("2024-04-20", program)
        )

    def test_true_when_order_date_is_after_completion(self):
        program = {"uuid": "pp-1", "date_completed": "2024-05-01T00:00:00.000+0500"}
        self.assertTrue(
            cu.lab_order_date_after_program_completion("2024-05-02", program)
        )

    def test_false_when_order_date_missing(self):
        program = {"uuid": "pp-1", "date_completed": "2024-05-01T00:00:00.000+0500"}
        self.assertFalse(cu.lab_order_date_after_program_completion("", program))


class TestGetCustomLabOrder(TestCase):
    def test_includes_patient_program_when_present(self):
        result = cu.get_custom_lab_order(
            _full_order({"uuid": "pp-1", "display": "MDR-TB Program"})
        )
        self.assertEqual(
            result["patientProgram"], {"uuid": "pp-1", "name": "MDR-TB Program"}
        )

    def test_patient_program_is_none_when_the_key_is_missing(self):
        result = cu.get_custom_lab_order(_full_order())
        self.assertIsNone(result["patientProgram"])

    def test_patient_program_is_none_when_the_value_is_null(self):
        result = cu.get_custom_lab_order(_full_order(patient_program=None))
        self.assertIsNone(result["patientProgram"])

    def test_patient_program_name_falls_back_to_empty_string(self):
        result = cu.get_custom_lab_order(_full_order({"uuid": "pp-1"}))
        self.assertEqual(result["patientProgram"], {"uuid": "pp-1", "name": ""})

    def test_keeps_the_other_fields_unchanged(self):
        result = cu.get_custom_lab_order(_full_order())
        self.assertEqual(result["labref"], "20240101-1")
        self.assertEqual(result["labtesttype"]["testGroup"], "BACTERIOLOGY")
        self.assertEqual(result["careSetting"]["name"], "Outpatient")

    def test_includes_the_order_date_activated(self):
        result = cu.get_custom_lab_order(
            _full_order(date_activated="2024-03-15T00:00:00.000+0500")
        )
        self.assertEqual(
            result["order"]["date_activated"], "2024-03-15T00:00:00.000+0500"
        )
