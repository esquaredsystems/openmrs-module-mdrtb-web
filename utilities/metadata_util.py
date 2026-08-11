import re
from utilities import common_utils as u
from utilities import restapi_utils as ru
from utilities import messages_util as msg
from utilities import commonlab_util as clu
from resources.enums.constants import Constants
from django.core.cache import caches
from django.utils.safestring import SafeString as ss
from urllib.parse import urlencode
import logging
import zlib
import pickle
from datetime import datetime


logger = logging.getLogger("django")

metadata_cache = caches["metadata"]

SYSTEM_DEVELOPER_ROLE = "System Developer"


def get_global_msgs(message_code, locale=None, default=None, source=None):
    """
    The translated label for a message code.

    Reads the Redis-cached messages loaded from the MDR-TB module's
    message_properties table (utilities/messages_util.py). Until 2026-08-04 this
    opened a .properties file and scanned it line by line on every single call,
    with a page performing over a thousand calls; those files no longer exist.

    `source` is accepted and ignored. It used to pick between the mdrtb,
    OpenMRS and commonlab property files; all three now live in one table, so
    the ~300 call sites using get_message_openMRS keep working unchanged.

    Returns the code itself when there is no translation, which is what the
    old reader did and makes a gap visible on screen.
    """
    return msg.lookup(message_code, locale=locale, default=default)


def _concepts_cache_key(locale):
    return f"concepts_{locale}"


def _get_cached_concepts(locale):
    compressed_concepts = metadata_cache.get(_concepts_cache_key(locale))
    if not compressed_concepts:
        return None
    return pickle.loads(zlib.decompress(compressed_concepts))


def _set_cached_concepts(locale, concepts):
    metadata_cache.set(_concepts_cache_key(locale), zlib.compress(pickle.dumps(concepts)))


def get_all_concepts(req):
    locale = req.session["locale"]
    if _get_cached_concepts(locale) is not None:
        return
    try:
        logger.debug(f"Fetching concepts in {locale}")
        status, response = ru.get(
            req,
            "concept",
            {
                "v": "custom:(uuid,display,name:(display,uuid,locale,conceptNameType),names:(display,name,uuid,locale,conceptNameType),answers:(uuid,display,name:(display,uuid,locale,conceptNameType),names:(display,uuid,locale,conceptNameType)))",
                "lang": locale,
            },
        )

        if status:
            _set_cached_concepts(locale, response["results"])
    except Exception:
        pass


def get_concept_from_cache(locale, uuid=None, name=None):
    """
    Retrieves a concept from the cache based on the provided UUID.

    Parameters:
    - locale (str): The locale whose cached concept list should be searched.
    - uuid (str): The UUID of the concept to retrieve.

    Returns:
    - tuple: A tuple consisting of a boolean value indicating the presence of the concept (True/False)
             and the concept itself. If the concept is found, the boolean value is True and the concept is returned.
             If the concept is not found, the boolean value is False and an empty dictionary is returned.

    Example:
        get_concept_from_cache("ru", "abc123")
    (True, {"uuid": "abc123", "name": "Concept Name", ...})
    """
    concepts = _get_cached_concepts(locale) or []
    if name:
        for concept in concepts:
            for concept_name in concept["names"]:
                if concept_name["locale"] == "en" and concept_name["name"] == name:
                    return bool(concept), concept
        return False, {}
    concept = next((c for c in concepts if c["uuid"] == uuid), {})
    return bool(concept), concept


def get_concept(req, uuid, lang=None):
    """
    Retrieves a concept from the cache or by making a request to the server if not found in the cache.

    Parameters:
    - req: The request object.
    - uuid (str): The UUID of the concept to retrieve.

    Returns:
    - dict: The retrieved concept as a dictionary.

    Raises:
    - Exception: If an error occurs while retrieving the concept.

    Example:
    >>> get_concept(request, "abc123")
    {"uuid": "abc123", "name": "Concept Name", ...}
    """
    locale = req.session["locale"]
    found, concept = get_concept_from_cache(locale, uuid=uuid)
    if found:
        return concept
    try:
        status, response = ru.get(
            req, f"concept/{uuid}", {"lang": locale, "v": "full"}
        )
        if status:
            concepts = _get_cached_concepts(locale) or []
            concepts.append(response)
            _set_cached_concepts(locale, concepts)
            return response
    except Exception as e:
        raise Exception(str(e))


def get_concept_by_search(req, query):
    try:
        locale = req.session["locale"]
        found, concept = get_concept_from_cache(locale, uuid=None, name=query)
        if found:
            return concept
        status, response = ru.get(
            req, "concept", {"lang": locale, "v": "full", "q": query}
        )
        if status:
            concepts = _get_cached_concepts(locale) or []
            for concept in response["results"]:
                for name in concept["names"]:
                    if name["locale"] == "en" and name["name"] == query:
                        concepts.append(concept)
                        _set_cached_concepts(locale, concepts)
                        return concept

    except Exception as e:
        raise Exception(e)


def get_location(req, uuid, representation=None):
    """
    Retrieves location information from the server based on the given UUID.

    Parameters:
    - req: The request object.
    - uuid (str): The UUID of the location to retrieve.

    Returns:
    - dict: A dictionary containing the location information, including the location name and its parent location.

    Raises:
    - Exception: If an error occurs while retrieving the location.

    Example:
        get_location(request, "abc123")
    {"location": "Location Name", "parent": "Parent Location Name"}
    """

    try:
        status, response = ru.get(req, f"location/{uuid}", {"v": "full"})

        if status:
            if representation == "FULL":
                return response
            else:
                return {
                    "location": response["display"],
                    "parent": response["parentLocation"]["display"]
                    if response["parentLocation"] is not None
                    else None,
                    "grandparent": response["parentLocation"]["parentLocation"][
                        "display"
                    ]
                    if response["parentLocation"] is not None
                    and response["parentLocation"]["parentLocation"] is not None
                    else None,
                }
    except Exception as e:
        raise Exception(str(e))


def get_user(req, username):
    """
    Retrieves user information based on the provided username.

    Parameters:
        req (object): Request object representing the current request.
        username (str): The username of the user to retrieve information for.

    Returns:
        dict: User information as a dictionary.

    Raises:
        Exception: If the request to retrieve user information fails.
    """

    status, response = ru.get(req, "user", {"q": username, "v": "full"})
    if status:
        return response
    else:
        raise Exception("Cant find user")


def get_patient_identifier_types(req):
    """
    Retrieves a list of patient identifier types.

    Parameters:
        req (Request): The request object.

    Returns:
        list: A list of patient identifier types, each represented as a dictionary with 'uuid' and 'name' fields.

    Raises:
        Exception: If patient identifier types cannot be found.
    """

    status, response = ru.get(req, "patientidentifiertype", {"v": "custom:(uuid,name)"})
    if status:
        return response["results"]
    else:
        raise Exception("Cant find patient identifier types")


def get_global_properties(req, key):
    """
    Retrieves the value of a global property.

    Parameters:
        req (Request): The request object.
        key (str): The key of the global property.

    Returns:
        str: The value of the global property.

    Raises:
        Exception: If the global property cannot be found or an error occurs.
    """
    try:
        status, response = ru.get(req, "systemsetting", {"q": key, "v": "full"})
        if status:
            return response["results"][0]["value"]
    except Exception as e:
        raise Exception(e)


def is_system_developer(req):
    """
    True when the logged-in user may modify administration data
    (Manage Locations / Users / Translations).

    The 'admin' account is always allowed. Roles are matched on both "name" and
    "display" because GET /session returns roles in ref representation, which
    carries display but often no name.

    Reads the session only - no REST call - so it is cheap enough for the
    context processor to call on every page render.
    """
    logged_user = req.session.get("logged_user") or {}
    user = logged_user.get("user") or {}
    if user.get("systemId") == "admin":
        return True
    for role in user.get("roles") or []:
        if role.get("name") == SYSTEM_DEVELOPER_ROLE:
            return True
        if role.get("display") == SYSTEM_DEVELOPER_ROLE:
            return True
    return False


def check_if_user_has_privilege(req, privilege_to_check, user_privileges):
    """
    Checks if a user has a specific privilege.

    privilege_to_check is the privilege's name as OpenMRS spells it, e.g.
    "Add Patients" - the values in resources/enums/privileges.py. Matching used
    to be on UUID, but privilege UUIDs are regenerated when the server is
    redeployed, which silently turned every check False and hid whole screens.
    Names are stable across deployments.

    Both "display" and "name" are checked: GET /session returns privileges in
    ref representation, which carries display but no name.

    Parameters:
        req (Request): The request object.
        privilege_to_check (str): The privilege name to look for.
        user_privileges (list): A list of user privileges.

    Returns:
        bool: True if the user has the privilege, False otherwise.
    """
    # Admins and System Developers get every privilege.
    if is_system_developer(req):
        return True
    for privilege in user_privileges or []:
        if privilege.get("display") == privilege_to_check:
            return True
        if privilege.get("name") == privilege_to_check:
            return True
    return False


def get_encounter_by_uuid(req, uuid):
    """
    Retrieves an encounter by its UUID.

    Parameters:
        req (Request): The request object.
        uuid (str): The UUID of the encounter to retrieve.

    Returns:
        dict: The encounter information if found, None otherwise.
    """
    try:
        status, response = ru.get(req, f"encounter/{uuid}", {"v": "full"})
        if status:
            return response
    except Exception:
        return None


def get_provider(req, username):
    """
    Retrieves provider information based on the provided username (provider identifier).

    Parameters:
        req (object): Request object representing the current request.
        username (str): The username of the user to retrieve information for.

    Returns:
        dict: User information as a dictionary.

    Raises:
        Exception: If the request to retrieve user information fails.
    """

    status, response = ru.get(req, "provider", {"q": username, "v": "full"})
    if status:
        return response
    else:
        raise Exception("Cant find provider")


def add_url_to_breadcrumb(req, name, query_params=None):
    """
    Adds a URL to the breadcrumb trail in the user's session.

    Parameters:
        req (Request): The request object.
        name (str): The name or label for the breadcrumb.
        query_params (dict, optional): Query parameters to include in the URL. Default is None.

    Raises:
        Exception: If there's an error while adding the URL to the breadcrumb.

    Note:
        The function modifies the `req.session` object to update the breadcrumb trail.
    """
    try:
        breadcrumbs = req.session.get("breadcrumbs", [])
        url = req.path_info
        if query_params:
            url += "?" + urlencode(query_params)
        index = None
        for i, bc in enumerate(breadcrumbs):
            if bc["name"] == name:
                index = i
                break
        if index is not None:
            breadcrumbs = breadcrumbs[: index + 1]
        else:
            breadcrumbs.append({"name": name, "url": url})
        req.session["breadcrumbs"] = breadcrumbs
    except Exception as e:
        raise Exception(e)


# def get_all_attribute_types(req):
#     common_test_attribute_types = zlib.compress(
#         pickle.dumps(
#             clu.get_attributes_of_labtest(req, {"uuid": Constants.COMMON_TEST.value})
#         )
#     )
#     dst_lj_attribute_types = zlib.compress(
#         pickle.dumps(clu.get_all_attribute_types(req, {"uuid": Constants.DST_LJ.value}))
#     )
#     dst_mgit_attribute_types = zlib.compress(
#         pickle.dumps(
#             clu.get_all_attribute_types(req, {"uuid": Constants.DST_MGIT.value})
#         )
#     )

#     cache.set("COMMONTEST_attribute_types", common_test_attribute_types, timeout=None)
#     cache.set("DST_LJ_attribute_types", common_test_attribute_types, timeout=None)
#     cache.set("DST_MGIT_attribute_types", common_test_attribute_types, timeout=None)
