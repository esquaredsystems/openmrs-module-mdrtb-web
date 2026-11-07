"""
Tests for Administration -> Manage Concepts (utilities/concepts_util.py) and the
concept-cache refresh it triggers (metadata_util.refresh_cached_concept).

No OpenMRS needed: the REST helpers are replaced by fakes that record every call,
so each test also proves which calls are NOT made.
"""
import unittest
from unittest import mock

from django.http import QueryDict

# restapi_utils first, as app/views.py does: rest_admin -> restapi_utils -> locations_util -> rest_admin
# is an existing circular import that only resolves in that order.
import utilities.restapi_utils  # noqa: F401
import utilities.concepts_util as cu
import utilities.metadata_util as mu

CONCEPT = {
    "uuid": "c1",
    "datatype": {"uuid": "dt-coded", "name": "Coded"},
    "conceptClass": {"uuid": "cls1"},
    "names": [
        {"uuid": "n-en", "name": "AFTER FAILURE", "locale": "en", "conceptNameType": "FULLY_SPECIFIED"},
        {"uuid": "n-en-short", "name": "AF", "locale": "en", "conceptNameType": "SHORT"},
        {"uuid": "n-ru", "name": "ПОСЛЕ НЕУДАЧИ", "locale": "ru", "conceptNameType": "FULLY_SPECIFIED"},
        {"uuid": "n-syn", "name": "synonym", "locale": "en", "conceptNameType": None},
    ],
    "descriptions": [{"uuid": "d-en", "description": "Patient who", "locale": "en"}],
    "answers": [{"uuid": "a1"}, {"uuid": "a2"}],
    "mappings": [{"conceptReferenceTerm": {"code": "17", "conceptSource": {"uuid": "src"}}}],
}

CLASSES = [{"uuid": "cls1", "display": "Misc"}, {"uuid": "cls2", "display": "Question"}]

DATATYPES = [
    {"uuid": "dt-num", "name": "Numeric"},
    {"uuid": "dt-text", "name": "Text"},
    {"uuid": "dt-coded", "name": "Coded"},
    {"uuid": "dt-bool", "name": "Boolean"},
]


REFERENCE = {"datatypes": DATATYPES, "classes": CLASSES}


def form(concept=CONCEPT, keep=None, add=(), **changes):
    """The page's single form exactly as rendered for `concept` (nothing changed), plus `changes`."""
    post = QueryDict(mutable=True)
    for field in ("full_name", "short_name", "description"):
        for lang in cu.SUPPORTED_LANGS:
            post[f"{field}_{lang}"] = ""
    for row in cu.translation_rows(concept):
        post[f"full_name_{row['locale']}"] = row["full_name"]
        post[f"short_name_{row['locale']}"] = row["short_name"]
        post[f"description_{row['locale']}"] = row["description"]
    post["concept_class"] = concept["conceptClass"]["uuid"]
    post["datatype"] = concept["datatype"]["uuid"]
    post.update({"map_type": "mt", "source": "", "code": ""})
    if concept["datatype"]["name"] == "Coded":
        post["answers_shown"] = "1"
        post.setlist("keep_answers", [a["uuid"] for a in concept["answers"]] if keep is None else keep)
        post.setlist("add_answers", list(add))
    for key, value in changes.items():
        post[key] = value
    return post


class FakeRest:
    def __init__(self, get_results=None):
        self.calls = []
        self.get_results = get_results or {}

    def get(self, req, endpoint, params=None):
        self.calls.append(("GET", endpoint, params))
        result = self.get_results.get((endpoint, (params or {}).get("lang")))
        if isinstance(result, Exception):
            raise result
        return result

    def post(self, req, endpoint, payload):
        self.calls.append(("POST", endpoint, payload))
        return {"uuid": "new-term"}

    def delete(self, req, endpoint):
        self.calls.append(("DELETE", endpoint, None))

    def writes(self):
        return [c for c in self.calls if c[0] != "GET"]


class ConceptsUtilTest(unittest.TestCase):
    def setUp(self):
        self.rest = FakeRest()
        for name, fake in (("rest_get", self.rest.get), ("rest_post", self.rest.post), ("rest_delete", self.rest.delete)):
            patcher = mock.patch.object(cu, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    # ---- translations

    def test_rows_cover_every_language_and_ignore_synonyms(self):
        rows = cu.translation_rows(CONCEPT)
        self.assertEqual([r["locale"] for r in rows], ["en", "ru", "tj"])
        self.assertEqual(rows[0]["full_name"], "AFTER FAILURE")
        self.assertEqual(rows[0]["short_name"], "AF")
        self.assertEqual(rows[2]["full_name_uuid"], "")

    def save(self, concept=CONCEPT, **kwargs):
        return cu.save_concept(None, concept, form(concept, **kwargs), REFERENCE)

    def test_unchanged_form_writes_nothing(self):
        self.assertEqual(self.save(), ([], 0))
        self.assertEqual(self.rest.calls, [])

    def test_only_changed_fields_are_written(self):
        problems, changes = self.save(
            full_name_en="AFTER FAILURE 1",  # edit
            short_name_en="",  # clear -> void
            description_en="",  # clear -> delete
            full_name_tj="БАЪД АЗ НОКОМӢ",  # add
            short_name_ru="  КР  ",  # add, trimmed
        )
        self.assertEqual((problems, changes), ([], 5))
        writes = self.rest.writes()
        self.assertIn(("POST", "concept/c1/name/n-en", {"name": "AFTER FAILURE 1"}), writes)
        self.assertTrue(any(w[0] == "DELETE" and w[1].startswith("concept/c1/name/n-en-short?reason=") for w in writes))
        self.assertIn(("DELETE", "concept/c1/description/d-en", None), writes)
        self.assertIn(
            ("POST", "concept/c1/name", {"name": "БАЪД АЗ НОКОМӢ", "locale": "tj", "conceptNameType": "FULLY_SPECIFIED"}),
            writes,
        )
        self.assertIn(("POST", "concept/c1/name", {"name": "КР", "locale": "ru", "conceptNameType": "SHORT"}), writes)

    def test_one_refused_part_means_nothing_is_written(self):
        # Valid translation + answer changes, but the class is not allowed -> no call at all.
        problems, changes = self.save(full_name_tj="НОМ", keep=["a1"], concept_class="cls-frequency")
        self.assertEqual((problems, changes), (["mdrtb.concepts.classNotAllowed"], 0))
        self.assertEqual(self.rest.calls, [])

    def test_existing_full_name_cannot_be_cleared(self):
        self.assertEqual(self.save(full_name_ru="", short_name_en="X"), (["mdrtb.concepts.fullNameRequired"], 0))
        self.assertEqual(self.rest.calls, [])

    def test_partial_failure_says_how_much_was_saved(self):
        def post(req, endpoint, payload):
            self.rest.calls.append(("POST", endpoint, payload))
            if len(self.rest.calls) == 2:
                raise Exception("Duplicate name")

        with mock.patch.object(cu, "rest_post", post):
            with self.assertRaisesRegex(Exception, "1 earlier change"):
                self.save(full_name_en="N1", full_name_ru="N2")

    # ---- class and datatype

    def test_numeric_complex_boolean_are_locked_both_ways(self):
        no_answers = dict(CONCEPT, answers=[])
        self.assertEqual(self.save(no_answers, datatype="dt-num"), (["mdrtb.concepts.datatypeLocked"], 0))
        numeric = dict(CONCEPT, answers=[], datatype={"uuid": "dt-num", "name": "Numeric"})
        self.assertEqual(self.save(numeric, datatype="dt-text"), (["mdrtb.concepts.datatypeLocked"], 0))
        self.assertEqual(self.rest.calls, [])

    def test_disabled_datatype_select_sends_nothing(self):
        numeric = dict(CONCEPT, answers=[], datatype={"uuid": "dt-num", "name": "Numeric"})
        post = form(numeric)
        del post["datatype"]  # a disabled <select> is not submitted
        self.assertEqual(cu.save_concept(None, numeric, post, REFERENCE), ([], 0))
        self.assertEqual(self.rest.calls, [])

    def test_coded_keeping_answers_cannot_change_datatype(self):
        self.assertEqual(self.save(datatype="dt-text"), (["mdrtb.concepts.removeAnswersFirst"], 0))

    def test_untick_all_answers_and_leave_coded_in_one_save(self):
        self.assertEqual(self.save(keep=[], datatype="dt-text"), ([], 2))
        self.assertEqual(
            self.rest.writes(),
            [("POST", "concept/c1", {"answers": []}), ("POST", "concept/c1", {"datatype": "dt-text"})],
        )

    def test_class_and_datatype_saved_together(self):
        no_answers = dict(CONCEPT, answers=[])
        self.assertEqual(self.save(no_answers, concept_class="cls2", datatype="dt-text"), ([], 1))
        self.assertEqual(self.rest.writes(), [("POST", "concept/c1", {"conceptClass": "cls2", "datatype": "dt-text"})])

    def test_class_outside_the_allowed_list_is_refused(self):
        self.assertEqual(self.save(concept_class="cls-frequency"), (["mdrtb.concepts.classNotAllowed"], 0))
        self.assertEqual(self.rest.calls, [])

    def test_dropdown_offers_only_the_allowed_classes(self):
        rows = [{"uuid": n, "display": n} for n in ("Anatomy", "Frequency", "Misc", "Misc Order", "Symptom/Finding", "Test")]
        with mock.patch.object(cu, "get_all_pages", lambda req, endpoint, params=None: rows if endpoint == "conceptclass" else []):
            classes = cu.get_reference_data(None)["classes"]
        self.assertEqual([c["display"] for c in classes], ["Misc", "Symptom/Finding", "Test"])

    # ---- answers

    def test_answers_keep_order_and_append_new(self):
        self.assertEqual(self.save(keep=["a2"], add=["a3", "a2"]), ([], 1))
        self.assertEqual(self.rest.writes(), [("POST", "concept/c1", {"answers": ["a2", "a3"]})])

    def test_answer_rules(self):
        self.assertEqual(self.save(add=["c1"]), (["mdrtb.concepts.answerIsSelf"], 0))
        self.assertEqual(self.rest.calls, [])

    def test_answers_untouched_when_list_not_on_page(self):
        text = dict(CONCEPT, datatype={"uuid": "dt-text", "name": "Text"}, answers=[])
        self.assertEqual(self.save(text), ([], 0))
        self.assertEqual(self.rest.calls, [])

    # ---- mappings

    def test_empty_mapping_fields_add_nothing(self):
        self.assertEqual(self.save(), ([], 0))
        self.assertEqual(self.rest.calls, [])

    def test_half_filled_mapping_refused(self):
        self.assertEqual(self.save(code="99"), (["mdrtb.concepts.mappingIncomplete"], 0))

    def test_duplicate_mapping_refused(self):
        self.assertEqual(self.save(source="src", code="17"), (["mdrtb.concepts.mappingExists"], 0))
        self.assertEqual(self.rest.calls, [])

    def test_term_matched_by_name_only_is_not_reused(self):
        self.rest.get_results[("conceptreferenceterm", None)] = {"results": [{"uuid": "t-x", "code": "OTHER"}]}
        self.assertEqual(self.save(source="src", code="99"), ([], 1))
        self.assertEqual(
            self.rest.writes(),
            [
                ("POST", "conceptreferenceterm", {"code": "99", "conceptSource": "src"}),
                ("POST", "concept/c1/mapping", {"conceptReferenceTerm": "new-term", "conceptMapType": "mt"}),
            ],
        )

    def test_existing_term_is_reused(self):
        self.rest.get_results[("conceptreferenceterm", None)] = {"results": [{"uuid": "t1", "code": "abc"}]}
        self.assertEqual(self.save(source="src", code="ABC"), ([], 1))
        self.assertEqual(
            self.rest.writes(), [("POST", "concept/c1/mapping", {"conceptReferenceTerm": "t1", "conceptMapType": "mt"})]
        )

    # ---- search

    def test_search_runs_every_language_session_language_last(self):
        self.rest.get_results.update(
            {
                ("concept", "en"): {"results": [{"uuid": "x", "display": "b"}]},
                ("concept", "tj"): {"results": [{"uuid": "y", "display": "A"}]},
                ("concept", "ru"): {"results": [{"uuid": "x", "display": "b"}]},
            }
        )
        results, truncated = cu.search_concepts(None, "q", "ru")
        self.assertEqual([c["uuid"] for c in results], ["y", "x"])
        self.assertFalse(truncated)
        self.assertEqual([c[2]["lang"] for c in self.rest.calls], ["en", "tj", "ru"])

    def test_results_are_named_in_the_system_language_whichever_language_matched(self):
        names = [
            {"name": "ПОСЛЕ НЕУДАЧИ", "locale": "ru", "conceptNameType": "FULLY_SPECIFIED", "localePreferred": True},
            {"name": "БАЪД АЗ НОКОМӢ", "locale": "tj", "conceptNameType": "FULLY_SPECIFIED", "localePreferred": True},
            {"name": "AFTER FAILURE", "locale": "en", "conceptNameType": "FULLY_SPECIFIED", "localePreferred": True},
        ]
        # Found first by the Russian search, so OpenMRS sent a Russian display.
        self.rest.get_results[("concept", "ru")] = {"results": [{"uuid": "x", "display": "ПОСЛЕ НЕУДАЧИ", "names": names}]}
        results, _ = cu.search_concepts(None, "q", "tj")
        self.assertEqual(results[0]["display"], "БАЪД АЗ НОКОМӢ")
        results, _ = cu.search_concepts(None, "q", "en_GB")
        self.assertEqual(results[0]["display"], "AFTER FAILURE")

    def test_localized_name_fallbacks(self):
        concept = {
            "display": "ru display",
            "names": [
                {"name": "SHORT", "locale": "tj", "conceptNameType": "SHORT"},
                {"name": "TJ SYNONYM", "locale": "tj", "conceptNameType": None, "localePreferred": True},
                {"name": "EN FULL", "locale": "en", "conceptNameType": "FULLY_SPECIFIED"},
                {"name": "OLD", "locale": "ru", "conceptNameType": "FULLY_SPECIFIED", "voided": True},
            ],
        }
        self.assertEqual(cu.localized_name(concept, "tj"), "TJ SYNONYM")  # preferred in that language
        self.assertEqual(cu.localized_name(concept, "ru"), "EN FULL")  # no Russian name -> English full name
        self.assertEqual(cu.localized_name({"display": "D", "names": []}, "ru"), "D")

    def test_unknown_uuid_is_an_empty_result(self):
        uuid = "31b5b644-0370-102d-b0e3-001ec94a0cc1"
        self.rest.get_results[(f"concept/{uuid}", None)] = Exception("404")
        self.assertEqual(cu.search_concepts(None, uuid, "ru"), ([], False))


class RefreshCachedConceptTest(unittest.TestCase):
    def setUp(self):
        self.store = {}
        self.req = mock.Mock()
        self.req.session = {"locale": "ru"}
        for name, fake in (
            ("_get_cached_concepts", lambda locale: self.store.get(locale)),
            ("_set_cached_concepts", lambda locale, concepts: self.store.__setitem__(locale, concepts)),
        ):
            patcher = mock.patch.object(mu, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(mu.metadata_cache, "delete", lambda key: self.store.pop(key.split("_", 1)[1], None))
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake_get(self, req, endpoint, params):
        shape = "full" if params["v"] == "full" else "short"
        return True, {
            "uuid": "c1",
            "display": f"NEW {params['lang']} {shape}",
            "name": {"display": "NEW", "uuid": "n2", "locale": params["lang"], "conceptNameType": "FULLY_SPECIFIED"},
            "names": [{"display": "NEW", "name": "NEW", "uuid": "n2", "locale": params["lang"], "conceptNameType": "FULLY_SPECIFIED"}],
            **({"datatype": {"display": "Coded"}} if shape == "full" else {}),
        }

    def test_replaces_concept_in_its_own_shape_and_inside_answers(self):
        self.store["ru"] = [
            {"uuid": "c1", "display": "OLD", "datatype": {}},  # added by get_concept (v=full)
            {"uuid": "q", "display": "Q", "answers": [{"uuid": "c1", "display": "OLD", "extra": 1}, {"uuid": "z"}]},
        ]
        self.store["en"] = [{"uuid": "q", "answers": [{"uuid": "c1", "display": "OLD"}]}]
        with mock.patch.object(mu.ru, "get", self.fake_get):
            mu.refresh_cached_concept(self.req, "c1")

        self.assertEqual(self.store["ru"][0]["display"], "NEW ru full")
        answer = self.store["ru"][1]["answers"][0]
        self.assertEqual(answer["display"], "NEW ru short")
        self.assertEqual(answer["extra"], 1)  # merged, not replaced
        self.assertEqual(self.store["ru"][1]["answers"][1], {"uuid": "z"})
        # Not cached in "en" itself, so it is not added there - only the answer copy changes.
        self.assertEqual([c["uuid"] for c in self.store["en"]], ["q"])
        self.assertEqual(self.store["en"][0]["answers"][0]["display"], "NEW en short")

    def test_unreadable_language_drops_that_list(self):
        self.store["tj"] = [{"uuid": "c1", "display": "OLD"}]
        with mock.patch.object(mu.ru, "get", side_effect=Exception("down")):
            mu.refresh_cached_concept(self.req, "c1")
        self.assertNotIn("tj", self.store)


if __name__ == "__main__":
    unittest.main()
