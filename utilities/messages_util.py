"""
UI translations, read from OpenMRS and cached in Redis.

Until 2026-08-04 every label was read from .properties files shipped inside this
app: get_global_msgs() opened a file and scanned it line by line on EVERY
lookup, and a single page performs over a thousand lookups. Those files are gone.
Messages now live in the MDR-TB module's message_properties table and are
reached through /ws/rest/v1/mdrtb/messageproperty.

Caching, so the change does not cost read time:

  Redis   one entry per language holding the whole {code: message} map, in the
          "metadata" cache next to concepts, with the same one-hour expiry.
          Filled at login (see warm()) and whenever a page finds it missing.
  Browser the same map is handed to the browser at login and kept in local
          storage, so client-side code does not call back for labels.

lookup() deliberately takes NO request: it only ever reads Redis, so a template
rendering a thousand labels cannot trigger a REST call. Filling the cache needs
a request and happens in warm().
"""

import logging
import pickle
import re
import time
import zlib

from urllib.parse import quote

from django.core.cache import caches

logger = logging.getLogger("django")

metadata_cache = caches["metadata"]

ENDPOINT = "mdrtb/messageproperty"

# The seeder records the unsuffixed bundle as "en"; the app offers en/ru/tj.
DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "ru", "tj")

# Some stored messages contain markup (OpenMRS core ships <b>, <a href>, ...).
# Labels are rendered as text, so tags are stripped exactly as the old
# properties-file reader did.
_TAG = re.compile("<.*?>")

SHEET_TTL = 30  # seconds

_SHEET_VERSION_KEY = "messages_sheet_version"

# resources/messages{,_ru,_tj}.properties are the last resort, and they matter most on the LOGIN PAGE
_files = {}  # lang -> {code: message}


def normalise_lang(locale):
    """'en_GB'/None/'' -> 'en'; 'ru_RU' -> 'ru'. Unknown codes pass through."""
    if not locale:
        return DEFAULT_LANG
    lang = str(locale).strip().replace("-", "_").split("_")[0].lower()
    return lang or DEFAULT_LANG


def cache_key(lang):
    return f"messages_{normalise_lang(lang)}"


# In-process memo in front of Redis.
#
# lookup() is called once per label and a page renders over a thousand of them.
# Without this, every label meant a Redis round trip plus a zlib decompress and
# an unpickle - a thousand of each per page, which would have been slower than
# the .properties files this replaced. With it, a worker touches Redis about
# once a minute per language and every label is a plain dict hit.
#
# Each worker process holds its own copy, so an edit made in Manage Translations
# becomes visible within _LOCAL_TTL rather than instantly. That is why the TTL is
# short, and why invalidate() clears this too.
_LOCAL_TTL = 60  # seconds to trust a loaded map
_MISS_TTL = 5  # shorter, so a cold cache is retried soon but not per label
_local = {}  # lang -> (expires_at, mapping or None)


def get_cached(lang):
    """The {code: message} map for a language, or None when not cached."""
    lang = normalise_lang(lang)
    now = time.monotonic()

    memo = _local.get(lang)
    if memo and memo[0] > now:
        return memo[1]

    blob = metadata_cache.get(cache_key(lang))
    mapping = None
    if blob:
        try:
            mapping = pickle.loads(zlib.decompress(blob))
        except Exception as e:  # corrupt entry must not break every page
            logger.warning(f"Discarding unreadable message cache for {lang}: {e}")
            metadata_cache.delete(cache_key(lang))
            mapping = None

    _local[lang] = (now + (_LOCAL_TTL if mapping else _MISS_TTL), mapping)
    return mapping


def set_cached(lang, mapping):
    lang = normalise_lang(lang)
    metadata_cache.set(cache_key(lang), zlib.compress(pickle.dumps(mapping)))
    _local[lang] = (time.monotonic() + _LOCAL_TTL, mapping)


def invalidate(lang=None):
    """Drop one language, or all of them after an edit in Manage Translations."""
    for one in ([lang] if lang else SUPPORTED_LANGS):
        metadata_cache.delete(cache_key(normalise_lang(one)))
        _local.pop(normalise_lang(one), None)
    _bump_sheet_version()  # also retires every cached page of the editing sheet


def fetch(req, lang):
    """
    Reads every message for a language from OpenMRS.

    The endpoint is a plain Spring controller, not a REST resource, so it
    returns a bare JSON list rather than the usual {"results": [...]} envelope
    and is not subject to the absolute-limit page cap.
    """
    from utilities.rest_admin import rest_get  # local: avoids an import cycle

    lang = normalise_lang(lang)
    rows = rest_get(req, ENDPOINT, {"lang": lang}) or []
    mapping = {}
    for row in rows:
        code = (row or {}).get("code")
        if code:
            mapping[code] = row.get("message") or ""
    return mapping


def warm(req, locale=None, force=False):
    """
    Makes sure the user's language and English are cached. Called at login,
    and by any page that finds the cache cold.

    Never raises: a translation outage must not stop someone signing in or
    opening a patient record. Worst case the labels fall back to their codes.
    """
    langs = [normalise_lang(locale)]
    if DEFAULT_LANG not in langs:
        langs.append(DEFAULT_LANG)  # fallback language for missing keys

    for lang in langs:
        if not force and get_cached(lang) is not None:
            continue
        try:
            mapping = fetch(req, lang)
            if mapping:
                set_cached(lang, mapping)
                logger.info(f"Cached {len(mapping)} messages for '{lang}'")
            else:
                logger.warning(f"No messages returned for '{lang}'")
        except Exception as e:
            logger.error(f"Could not load messages for '{lang}': {e}")


def _file_messages(lang):
    lang = normalise_lang(lang)
    if lang in _files:
        return _files[lang]

    from utilities.common_utils import get_project_root

    name = "messages.properties" if lang == DEFAULT_LANG else f"messages_{lang}.properties"
    path = f"{get_project_root()}/resources/{name}"
    mapping = {}
    try:
        # Mode "r" is spelled out: these files are never opened for writing.
        with open(path, mode="r", encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                if key:
                    mapping[key] = value.strip()
        logger.info(f"Loaded {len(mapping)} fallback messages from {name}")
    except FileNotFoundError:
        logger.info(f"No fallback message file for '{lang}' ({name})")
    except Exception as e:
        logger.warning(f"Could not read fallback messages from {name}: {e}")

    _files[lang] = mapping
    return mapping


def reload_files():
    """Forget the parsed .properties files, so edits are picked up."""
    _files.clear()


def lookup(code, locale=None, default=None):
    """
    The translated label for a code.

    Order: cached language -> cached English -> the shipped .properties file for
    the language -> the English file -> the supplied default -> the code itself.

    The files come after the cache so an edit made in Manage Translations wins
    over the copy shipped with the app, but before the code, so a page rendered
    without a warm cache (the login screen) still shows real text.
    """
    if not code:
        raise Exception("Please provide a valid message code")

    code = code.strip()
    lang = normalise_lang(locale)

    value = (get_cached(lang) or {}).get(code)
    if not value and lang != DEFAULT_LANG:
        value = (get_cached(DEFAULT_LANG) or {}).get(code)
    if not value:
        value = _file_messages(lang).get(code)
    if not value and lang != DEFAULT_LANG:
        value = _file_messages(DEFAULT_LANG).get(code)
    if not value:
        value = default or code

    return _TAG.sub(" ", str(value)).strip() or code


def search(req, lang=None, q=None):
    """
    Labels matching a language and a code fragment, sorted by code.

    `q` is a case-insensitive substring of the CODE (not the text), matched by
    OpenMRS. It is what makes the screen usable: 'mdrtb.users.' lists that whole
    group, 'general.' lists the shared buttons. Without a filter this returns
    every label for the language (~1,700 rows) - the endpoint is a plain
    controller, so it is not subject to the REST page cap, but the screen still
    asks for a filter first rather than rendering the lot.
    """
    from utilities.rest_admin import rest_get

    params = {}
    if lang:
        params["lang"] = normalise_lang(lang)
    if q:
        params["q"] = q.strip()
    rows = rest_get(req, ENDPOINT, params) or []
    return sorted(rows, key=lambda r: ((r or {}).get("code") or "").lower())


# The sheet is paged, so the same rows are asked repeatedly while someone clicks through.
# Building it costs one REST call per language (~1,700 rows each), so the assembled sheet is cached 
def _sheet_version():
    return metadata_cache.get(_SHEET_VERSION_KEY) or 1


def _bump_sheet_version():
    try:
        metadata_cache.set(_SHEET_VERSION_KEY, _sheet_version() + 1, None)
    except Exception as e:
        logger.warning(f"Could not bump the translations sheet version: {e}")


def table(req, q=None):
    """
    Every code with its text in all languages, for the editing sheet:

        [{"code": "mdrtb.yes", "text": {"en": "Yes", "ru": "Да", "tj": ""}}, ...]

    The per-language dict is called "text", not "values": in a Django template
    `row.values` would be ambiguous with dict.values().

    Read straight from OpenMRS rather than the Redis cache: this is the screen
    where the values are edited, so it must show what is actually stored, not a
    copy that can be up to a minute old.
    """
    key = f"messages_sheet_{_sheet_version()}_{(q or '').lower()}"
    cached = metadata_cache.get(key)
    if cached:
        try:
            return pickle.loads(zlib.decompress(cached))
        except Exception:
            metadata_cache.delete(key)

    by_code = {}
    for lang in SUPPORTED_LANGS:
        for row in search(req, lang=lang, q=q):
            code = (row or {}).get("code")
            if not code:
                continue
            by_code.setdefault(code, {l: "" for l in SUPPORTED_LANGS})
            by_code[code][lang] = row.get("message") or ""
    rows = [
        {"code": code, "text": by_code[code]}
        for code in sorted(by_code, key=str.lower)
    ]
    try:
        metadata_cache.set(key, zlib.compress(pickle.dumps(rows)), SHEET_TTL)
    except Exception as e:
        logger.warning(f"Could not cache the translations sheet: {e}")
    return rows


def save_row(req, code, values, originals=None):
    """
    Saves one code across languages, spreadsheet style.

    Only languages whose text actually changed are written. Clearing a box
    deletes that language's row, so the screen falls back to English (or to the
    code) rather than storing an empty string that would render as a blank label.

    Returns (saved, removed) counts.
    """
    code = (code or "").strip()
    if not code:
        raise Exception("A code is required")
    originals = originals or {}
    saved = removed = 0

    for lang in SUPPORTED_LANGS:
        new = (values.get(lang) or "").strip()
        old = (originals.get(lang) or "").strip()
        if new == old:
            continue
        if new:
            save(req, lang, code, new)
            saved += 1
        elif old:
            try:
                delete(req, lang, code)
                removed += 1
            except Exception as e:
                # Nothing stored for that language is not an error here.
                logger.info(f"Could not remove {code} ({lang}): {e}")
    return saved, removed


def delete_row(req, code):
    """Removes a code from every language. Returns how many were removed."""
    removed = 0
    for lang in SUPPORTED_LANGS:
        try:
            delete(req, lang, code)
            removed += 1
        except Exception:
            pass  # not stored in that language
    return removed


def save(req, lang, code, message):
    """Creates or updates one label. POST upserts on the body's lang + code."""
    from utilities.rest_admin import rest_post

    lang = normalise_lang(lang)
    code = (code or "").strip()
    if not code:
        raise Exception("A code is required")
    result = rest_post(
        req, ENDPOINT, {"lang": lang, "code": code, "message": message or ""}
    )
    invalidate(lang)
    return result


def delete(req, lang, code):
    """
    Removes one stored label. Deletes only from message_properties - the shipped
    .properties file is read-only, so the label reverts to the text that ships
    with the app (then English, then the code).
    """

    from utilities.rest_admin import rest_delete

    lang = normalise_lang(lang)
    rest_delete(req, f"{ENDPOINT}/{quote(lang)}/{quote((code or '').strip())}")
    invalidate(lang)


def all_messages(locale=None):
    """
    The whole map for a language, English filled in behind it. Used for the
    copy handed to the browser at login.
    """
    merged = dict(get_cached(DEFAULT_LANG) or {})
    lang = normalise_lang(locale)
    if lang != DEFAULT_LANG:
        merged.update(get_cached(lang) or {})
    return merged
