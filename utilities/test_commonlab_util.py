import django
import os
from django.test import TestCase, RequestFactory
from unittest.mock import patch
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


class SummarizeLabOrderCollectionDateTest(TestCase):
    DATE_COLLECTED = {"code": "DATE COLLECTED", "datatype": "org.openmrs.customdatatype.datatype.DateDatatype"}

    def test_uses_the_date_collected_attribute(self):
        order = {
            "order": {"dateActivated": "2026-09-10T00:00:00.000+0500"},
            "attributes": [{"attributeType": self.DATE_COLLECTED, "valueReference": "2026-09-08 00:00:00"}],
        }
        self.assertEqual(cu.summarize_lab_order(order)["collection_date"], "2026-09-08")

    def test_falls_back_to_the_order_date_without_the_attribute(self):
        order = {"order": {"dateActivated": "2026-09-10T00:00:00.000+0500"}, "attributes": []}
        summary = cu.summarize_lab_order(order)
        self.assertEqual(summary["collection_date"], "2026-09-10")
        self.assertFalse(summary["dated"])

    def test_none_without_attribute_or_order_date(self):
        self.assertIsNone(cu.summarize_lab_order({"attributes": []})["collection_date"])


class LabOrderSampleStatusTest(TestCase):
    def test_accepted_wins_over_other_statuses(self):
        samples = [{"status": "REJECTED"}, {"status": "COLLECTED"}, {"status": "ACCEPTED"}]
        self.assertEqual(cu.lab_order_sample_status(samples, True), "accepted")

    def test_processed_counts_as_accepted(self):
        self.assertEqual(cu.lab_order_sample_status([{"status": "PROCESSED"}], True), "accepted")

    def test_collected_is_waiting_for_acceptance(self):
        samples = [{"status": "REJECTED"}, {"status": "COLLECTED"}]
        self.assertEqual(cu.lab_order_sample_status(samples, True), "collected")

    def test_rejected_when_every_sample_was_rejected(self):
        self.assertEqual(cu.lab_order_sample_status([{"status": "REJECTED"}], True), "rejected")

    def test_none_without_samples(self):
        self.assertEqual(cu.lab_order_sample_status([], True), "none")
        self.assertEqual(cu.lab_order_sample_status(None, False), "notRequired")


class FormatLabAttributeValueTest(TestCase):
    def _attribute(self, input_type, value, **extra):
        return {"attributeType": {"inputType": input_type, **extra}, "valueReference": value}

    def test_empty_values_are_none(self):
        self.assertIsNone(cu.format_lab_attribute_value(self._attribute("text", "")))
        self.assertIsNone(cu.format_lab_attribute_value({"attributeType": {"inputType": "text"}}))

    def test_coded_answer_shows_its_display_name(self):
        attribute = self._attribute("select", "a-2", answers=[
            {"uuid": "a-1", "display": "Negative"}, {"uuid": "a-2", "display": "Positive"}])
        self.assertEqual(cu.format_lab_attribute_value(attribute), "Positive")

    def test_date_is_day_month_year(self):
        attribute = self._attribute("date", "2020-09-04 00:00:00")
        self.assertEqual(cu.format_lab_attribute_value(attribute), "04.09.2020")

    def test_checkbox(self):
        self.assertEqual(cu.format_lab_attribute_value(self._attribute("checkbox", "on")), "✓")

    def test_text_is_unchanged(self):
        self.assertEqual(cu.format_lab_attribute_value(self._attribute("text", "3+")), "3+")


class GroupLabResultAttributesTest(TestCase):
    def test_splits_common_from_grouped_keeping_order(self):
        a = {"attributeType": {"group": None, "name": "a"}}
        b = {"attributeType": {"group": "XPERT", "name": "b"}}
        c = {"attributeType": {"group": "XPERT", "name": "c"}}
        common, grouped = cu.group_lab_result_attributes([a, b, c])
        self.assertEqual(common, [a])
        self.assertEqual(grouped, {"XPERT": [b, c]})


class FindLabOrderByOrderUuidTest(TestCase):
    RESULTS = {"results": [
        {"uuid": "lab-1", "order": {"uuid": "order-1"}},
        {"uuid": "lab-2", "order": {"uuid": "order-2"}},
    ]}

    def test_finds_the_lab_order_for_the_order(self):
        with patch.object(cu.ru, "get", return_value=(True, self.RESULTS)):
            self.assertEqual(cu.find_lab_order_by_order_uuid(None, "patient", "order-2"), "lab-2")

    def test_none_when_not_found_or_request_fails(self):
        with patch.object(cu.ru, "get", return_value=(True, self.RESULTS)):
            self.assertIsNone(cu.find_lab_order_by_order_uuid(None, "patient", "other"))
        with patch.object(cu.ru, "get", return_value=(False, {})):
            self.assertIsNone(cu.find_lab_order_by_order_uuid(None, "patient", "order-1"))


class CurrentLabSampleTest(TestCase):
    def test_prefers_the_accepted_sample(self):
        samples = [{"uuid": "a", "status": "COLLECTED"}, {"uuid": "b", "status": "ACCEPTED"}]
        self.assertEqual(cu.current_lab_sample(samples)["uuid"], "b")

    def test_processed_counts_as_accepted(self):
        samples = [{"uuid": "a", "status": "REJECTED"}, {"uuid": "b", "status": "PROCESSED"}]
        self.assertEqual(cu.current_lab_sample(samples)["uuid"], "b")

    def test_falls_back_to_the_waiting_sample(self):
        samples = [{"uuid": "a", "status": "REJECTED"}, {"uuid": "b", "status": "COLLECTED"}]
        self.assertEqual(cu.current_lab_sample(samples)["uuid"], "b")

    def test_none_when_only_rejected_or_empty(self):
        self.assertIsNone(cu.current_lab_sample([{"uuid": "a", "status": "REJECTED"}]))
        self.assertIsNone(cu.current_lab_sample(None))
