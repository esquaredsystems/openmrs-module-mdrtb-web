import logging
from resources.enums.constants import Constants
from utilities.common_utils import uuid_regex
from utilities.messages_util import SUPPORTED_LANGS, normalise_lang
from utilities.rest_admin import (
    SessionExpired,  # noqa: F401  (re-exported for the views)
    get_all_pages,
    rest_delete,
    rest_get,
    rest_post,
)

logger = logging.getLogger("django")

# Per-language search size. The server rejects any limit above its cap (100).
SEARCH_LIMIT = 50

CONCEPT_REP = (
    "custom:(uuid,display,set,retired,"
    "datatype:(uuid,display,name),"
    "conceptClass:(uuid,display,name),"
    "names:(uuid,name,locale,localePreferred,conceptNameType,voided),"
    "descriptions:(uuid,description,locale),"
    "answers:(uuid,display,retired),"
    "mappings:(uuid,conceptReferenceTerm:(uuid,code,name,conceptSource:(uuid,display)),"
    "conceptMapType:(uuid,display)))"
)

SEARCH_REP = (
    "custom:(uuid,display,retired,datatype:(display),conceptClass:(display),"
    "names:(name,locale,localePreferred,conceptNameType,voided))"
)


def localized_name(concept, locale):
    """
    The concept's name in the system language, the way OpenMRS picks it:
    preferred name in that language -> its full name -> English full name ->
    whatever OpenMRS sent as display. Search results are merged from several
    languages, so their own "display" can be in any of them.
    """
    lang = normalise_lang(locale)
    names = [n for n in concept.get("names") or [] if not n.get("voided")]
    for language in (lang, "en"):
        in_language = [n for n in names if normalise_lang(n.get("locale")) == language]
        preferred = next((n for n in in_language if n.get("localePreferred")), None)
        full = next((n for n in in_language if n.get("conceptNameType") == Constants.FULLY_SPECIFIED.value), None)
        if language == lang and preferred:
            return preferred.get("name")
        if full:
            return full.get("name")
    return concept.get("display") or ""


def get_concept(req, uuid, locale):
    # `lang` makes OpenMRS send every nested "display" (answers, class, ...) in
    # the system language.
    concept = rest_get(req, f"concept/{uuid}", {"v": CONCEPT_REP, "lang": normalise_lang(locale)})
    if not concept:
        return None
    # getNames() already excludes voided names; filtered again in case a
    # future OpenMRS version changes that.
    concept["names"] = [n for n in concept.get("names") or [] if not n.get("voided")]
    concept["display"] = localized_name(concept, locale)
    return concept


def search_concepts(req, query, session_locale):
    """
    Concepts whose name matches `query` in ANY language, or the one concept
    with that UUID.

    OpenMRS searches the request's locale plus the server's allowed-locale
    list only, so the search is run once per language and merged. The
    session's own language goes LAST: `lang` changes the locale of the
    OpenMRS session, and this leaves it where the rest of the app expects it.

    Returns (results, truncated). truncated = some language hit SEARCH_LIMIT.
    """
    query = (query or "").strip()
    if not query:
        return [], False

    if uuid_regex.fullmatch(query.lower()):
        try:
            concept = rest_get(
                req, f"concept/{query}", {"v": SEARCH_REP, "lang": normalise_lang(session_locale)}
            )
        except SessionExpired:
            raise
        except Exception as e:
            # An unknown uuid is a 404 - an empty result, not an error.
            logger.info(f"Concept lookup by uuid {query} found nothing: {e}")
            return [], False
        if not concept:
            return [], False
        concept["display"] = localized_name(concept, session_locale)
        return [concept], False

    session_lang = normalise_lang(session_locale)
    languages = [lang for lang in SUPPORTED_LANGS if lang != session_lang]
    languages.append(session_lang if session_lang in SUPPORTED_LANGS else SUPPORTED_LANGS[0])

    found = {}
    truncated = False
    for lang in languages:
        body = rest_get(
            req,
            "concept",
            {
                "q": query,
                "lang": lang,
                "includeAll": "true",  # retired concepts still need translations
                "v": SEARCH_REP,
                "limit": SEARCH_LIMIT,
            },
        )
        page = (body or {}).get("results", [])
        if len(page) >= SEARCH_LIMIT:
            truncated = True
        for concept in page:
            found.setdefault(concept["uuid"], concept)

    # Shown in the system language whichever language matched.
    for concept in found.values():
        concept["display"] = localized_name(concept, session_locale)
    results = sorted(found.values(), key=lambda c: (c.get("display") or "").lower())
    return results, truncated


def get_reference_data(req):
    """Dropdown lists for the edit page. Retired entries are never offered."""

    def active(endpoint):
        rows = get_all_pages(req, endpoint, {"v": "default"})
        rows = [r for r in rows if not r.get("retired")]
        return sorted(rows, key=lambda r: (r.get("display") or "").lower())

    return {
        "classes": [c for c in active("conceptclass") if c.get("display") in Constants.ALLOWED_CONCEPT_CLASSES.value],
        "datatypes": active("conceptdatatype"),
        "sources": active("conceptsource"),
        "map_types": active("conceptmaptype"),
    }


def _find(rows, name_type, locale):
    return next(
        (r for r in rows if r.get("conceptNameType") == name_type and r.get("locale") == locale),
        None,
    )


def translation_rows(concept):
    """One row per language: full name, short name, description (+ their uuids)."""
    names = concept.get("names") or []
    descriptions = concept.get("descriptions") or []
    rows = []
    for locale in SUPPORTED_LANGS:
        full = _find(names, Constants.FULLY_SPECIFIED.value, locale) or {}
        short = _find(names, Constants.SHORT.value, locale) or {}
        description = next((d for d in descriptions if d.get("locale") == locale), {})
        rows.append(
            {
                "locale": locale,
                "full_name": full.get("name") or "",
                "full_name_uuid": full.get("uuid") or "",
                "short_name": short.get("name") or "",
                "short_name_uuid": short.get("uuid") or "",
                "description": description.get("description") or "",
                "description_uuid": description.get("uuid") or "",
            }
        )
    return rows


def is_datatype_locked(datatype):
    return (datatype or {}).get("name") in Constants.LOCKED_DATATYPES.value


def save_concept(req, concept, post, reference):
    """
    The edit page's single Save. Every part is checked FIRST; if anything is
    refused, nothing at all is written and (problems, 0) is returned with
    message codes.

    Then only what changed is written, in this order:
      1. translations       (names / descriptions are subresources, one call each)
      2. answers            (before datatype, so "untick all answers + leave
                             Coded" works in one save)
      3. class and datatype (core re-checks the datatype against obs)
      4. new mapping        (only when the mapping fields were filled in)

    If a call fails, the earlier ones are already saved; the error says how
    many. Returns ([], number_of_changes).
    """
    problems = []
    plan = []

    for row in translation_rows(concept):
        locale = row["locale"]
        full = (post.get(f"full_name_{locale}") or "").strip()
        short = (post.get(f"short_name_{locale}") or "").strip()
        description = (post.get(f"description_{locale}") or "").strip()

        if len(full) > 255 or len(short) > 255:
            problems.append("mdrtb.concepts.nameTooLong")

        # Full name: edit or add. Clearing one is refused - OpenMRS would be
        # left with a voided fully specified name, which its validator rejects.
        if row["full_name_uuid"]:
            if not full:
                problems.append("mdrtb.concepts.fullNameRequired")
            elif full != row["full_name"]:
                plan.append(("POST", f"concept/{concept['uuid']}/name/{row['full_name_uuid']}", {"name": full}))
        elif full:
            plan.append(
                ("POST", f"concept/{concept['uuid']}/name",
                 {"name": full, "locale": locale, "conceptNameType": Constants.FULLY_SPECIFIED.value})
            )

        # Short name: edit, add, or void when cleared.
        if row["short_name_uuid"]:
            if not short:
                plan.append(
                    ("DELETE",
                     f"concept/{concept['uuid']}/name/{row['short_name_uuid']}"
                     f"?reason=Cleared%20in%20Manage%20Concepts", None)
                )
            elif short != row["short_name"]:
                plan.append(("POST", f"concept/{concept['uuid']}/name/{row['short_name_uuid']}", {"name": short}))
        elif short:
            plan.append(
                ("POST", f"concept/{concept['uuid']}/name",
                 {"name": short, "locale": locale, "conceptNameType": Constants.SHORT.value})
            )

        # Description: edit, add, or delete when cleared.
        if row["description_uuid"]:
            if not description:
                plan.append(("DELETE", f"concept/{concept['uuid']}/description/{row['description_uuid']}", None))
            elif description != row["description"]:
                plan.append(
                    ("POST", f"concept/{concept['uuid']}/description/{row['description_uuid']}",
                     {"description": description})
                )
        elif description:
            plan.append(
                ("POST", f"concept/{concept['uuid']}/description",
                 {"description": description, "locale": locale})
            )

    # The answer list is only on the page for Coded concepts.
    answers_after = [a["uuid"] for a in concept.get("answers") or []]
    if post.get("answers_shown"):
        if (concept.get("datatype") or {}).get("name") != Constants.CODED_DATATYPE.value:
            problems.append("mdrtb.concepts.notCoded")
        else:
            wanted = []
            for answer_uuid in post.getlist("keep_answers") + post.getlist("add_answers"):
                if answer_uuid and answer_uuid not in wanted:
                    wanted.append(answer_uuid)
            if concept["uuid"] in wanted:
                problems.append("mdrtb.concepts.answerIsSelf")
            elif wanted != answers_after:
                plan.append(("POST", f"concept/{concept['uuid']}", {"answers": wanted}))
                answers_after = wanted

    class_uuid = post.get("concept_class")
    datatype_uuid = post.get("datatype")
    current_class = (concept.get("conceptClass") or {}).get("uuid")
    current_datatype = concept.get("datatype") or {}
    payload = {}

    if class_uuid and class_uuid != current_class:
        if not any(c.get("uuid") == class_uuid for c in reference["classes"]):
            problems.append("mdrtb.concepts.classNotAllowed")
        else:
            payload["conceptClass"] = class_uuid

    if datatype_uuid and datatype_uuid != current_datatype.get("uuid"):
        new_datatype = next((d for d in reference["datatypes"] if d.get("uuid") == datatype_uuid), None)
        if new_datatype is None:
            problems.append("mdrtb.concepts.unknownDatatype")
        elif is_datatype_locked(current_datatype) or is_datatype_locked(new_datatype):
            problems.append("mdrtb.concepts.datatypeLocked")
        elif current_datatype.get("name") == Constants.CODED_DATATYPE.value and answers_after:
            problems.append("mdrtb.concepts.removeAnswersFirst")
        else:
            payload["datatype"] = datatype_uuid

    if payload:
        plan.append(("POST", f"concept/{concept['uuid']}", payload))

    source_uuid = post.get("source")
    code = (post.get("code") or "").strip()
    map_type_uuid = post.get("map_type")
    if source_uuid or code:
        already_mapped = any(
            ((m.get("conceptReferenceTerm") or {}).get("conceptSource") or {}).get("uuid") == source_uuid
            and ((m.get("conceptReferenceTerm") or {}).get("code") or "").lower() == code.lower()
            for m in concept.get("mappings") or []
        )
        if not source_uuid or not code or not map_type_uuid:
            problems.append("mdrtb.concepts.mappingIncomplete")
        elif already_mapped:
            problems.append("mdrtb.concepts.mappingExists")
        else:
            # Read now, so a retired term is refused before anything is written.
            # The search falls back to matching the term NAME, so the code is
            # compared again here before the term is reused.
            body = rest_get(
                req,
                "conceptreferenceterm",
                {"source": source_uuid, "codeOrName": code, "includeAll": "true", "v": "default"},
            )
            term_uuid = None
            for term in (body or {}).get("results", []):
                if (term.get("code") or "").lower() == code.lower():
                    if term.get("retired"):
                        raise Exception(
                            f"Reference term {code} exists in this source but is retired. "
                            "Restore it in OpenMRS first."
                        )
                    term_uuid = term["uuid"]
                    break
            plan.append(
                ("MAPPING", f"concept/{concept['uuid']}/mapping",
                 {"term": term_uuid, "source": source_uuid, "code": code, "map_type": map_type_uuid})
            )

    if problems:
        return sorted(set(problems)), 0

    done = 0
    for method, endpoint, payload in plan:
        try:
            if method == "DELETE":
                rest_delete(req, endpoint)
            elif method == "MAPPING":
                term_uuid = payload["term"]
                if term_uuid is None:
                    created = rest_post(
                        req, "conceptreferenceterm",
                        {"code": payload["code"], "conceptSource": payload["source"]},
                    )
                    term_uuid = created["uuid"]
                    logger.info(f"Created reference term {payload['code']} ({term_uuid})")
                rest_post(
                    req, endpoint,
                    {"conceptReferenceTerm": term_uuid, "conceptMapType": payload["map_type"]},
                )
            else:
                rest_post(req, endpoint, payload)
        except SessionExpired:
            raise
        except Exception as e:
            if done:
                raise Exception(f"{e} ({done} earlier change(s) were saved)")
            raise
        done += 1
    return [], done
