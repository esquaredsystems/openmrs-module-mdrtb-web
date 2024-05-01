import re
from utilities import common_utils as u
from utilities import restapi_utils as ru
from utilities import commonlab_util as clu
from resources.enums.constants import Constants
from django.core.cache import cache
from django.utils.safestring import SafeString as ss
from urllib.parse import urlencode
import logging
import zlib
import pickle
from datetime import datetime


logger = logging.getLogger("django")

# os.environ['DJANGO_SETTINGS_MODULE'] = 'mdrtb.settings'
# django.setup()


def get_global_msgs(message_code, locale=None, default=None, source=None):
    # No messages file for en_GB
    """
    Retrieves a global message based on the provided message code.

    It looks for the message code in different message files based on the locale, source, and default properties file names.
    It uses the u.get_project_root function to determine the project root directory.

    Parameters:
    - message_code (str): The code of the message to retrieve.
    - locale (str, optional): The locale code. Defaults to None.
    - default (str, optional): The default value to return if the message code is not found. Defaults to None.
    - source (str, optional): The source of the message. Can be "OpenMRS" or "commonlab". Defaults to None.

    Returns:
    - str: The retrieved global message.
           Returns the message code itself if the corresponding message is not found.

    Raises:
    - Exception: If no message code is provided.

    Example:
        get_global_msgs("mdrtb.allCasesEnrolled", locale="en_US", source="OpenMRS")
    "All cases enrolled"
    """

    if message_code:
        value = ""
        dir = f"{u.get_project_root()}/resources"
        if source is None:
            if locale is None or locale == "en_GB" or locale == "en":
                file = f"{dir}/messages.properties"
            else:
                file = f"{dir}/messages_{locale}.properties"

        if source == "OpenMRS":
            if locale is None or locale == "en_GB" or locale == "en":
                file = f"{dir}/openMRS_messages.properties"
            else:
                file = f"{dir}/openMRS_messages_{locale}.properties"

        if source == "commonlab":
            if locale is None or locale == "en_GB" or locale == "en":
                file = f"{dir}/commonlab_messages.properties"
            else:
                file = f"{dir}/commonlab_messages_{locale}.properties"

        data = u.read_properties_file(file, "r", encoding="utf-8")
        if data is not None:
            for message in data:
                split_msg = message.split("=")
                if split_msg[0].strip() == message_code.strip():
                    value = split_msg[1]
                elif default:
                    value = default
        else:
            value = message_code
        if len(value) < 1:
            value = message_code
        cleaner = re.compile("<.*?>")
        return re.sub(cleaner, " ", value.strip())

    else:
        raise Exception("Please provide a valid message code")


def get_all_concepts(req):
    compressed_concepts = cache.get("concepts", [])
    if compressed_concepts:
        return pickle.loads(zlib.decompress(compressed_concepts))
    try:
        logger.info(f"Fetching concepts in {req.session['locale']}")
        status, response = ru.get(
            req,
            "concept",
            {
                "v": "custom:(uuid,display,name:(display,uuid,locale,conceptNameType),names:(display,name,uuid,locale,conceptNameType),answers:(uuid,display,name:(display,uuid,locale,conceptNameType),names:(display,uuid,locale,conceptNameType)))",
                "lang": req.session["locale"],
            },
        )

        if status:
            seralized_concepts = pickle.dumps(response["results"])
            compressed_concepts = zlib.compress(seralized_concepts)
            cache.set("concepts", compressed_concepts, timeout=None)
    except Exception:
        pass


def get_concept_from_cache(uuid=None, name=None):
    """
    Retrieves a concept from the cache based on the provided UUID.

    Parameters:
    - uuid (str): The UUID of the concept to retrieve.

    Returns:
    - tuple: A tuple consisting of a boolean value indicating the presence of the concept (True/False)
             and the concept itself. If the concept is found, the boolean value is True and the concept is returned.
             If the concept is not found, the boolean value is False and an empty dictionary is returned.

    Example:
        get_concept_from_cache("abc123")
    (True, {"uuid": "abc123", "name": "Concept Name", ...})
    """
    concepts = pickle.loads(zlib.decompress(cache.get("concepts", [])))
    if name:
        for concept in concepts:
            for concept_name in concept["names"]:
                if concept_name["locale"] == "en" and concept_name["name"] == name:
                    return bool(concept), concept
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

    found, concept = get_concept_from_cache(uuid=uuid)
    if found:
        return concept
    try:
        status, response = ru.get(
            req, f"concept/{uuid}", {"lang": req.session["locale"], "v": "full"}
        )
        if status:
            concepts = cache.get("concepts", [])
            concepts.append(response)
            cache.set("concepts", concepts, timeout=None)
            return response
    except Exception as e:
        raise Exception(str(e))


def get_concept_by_search(req, query):
    try:
        found, concept = get_concept_from_cache(uuid=None, name=query)
        if found:
            return concept
        status, response = ru.get(
            req, "concept", {"lang": req.session["locale"], "v": "full", "q": query}
        )
        if status:
            compressed_concepts = cache.get("concepts", [])
            if compressed_concepts:
                concepts = pickle.loads(zlib.decompress(compressed_concepts))
            else:
                concepts = compressed_concepts
            for concept in response["results"]:
                for name in concept["names"]:
                    if name["locale"] == "en" and name["name"] == query:
                        concepts.append(concept)
                        zlib.compress(pickle.dumps(concepts))
                        cache.set("concepts", concepts, timeout=None)
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
        status, response = ru.get(
            req, "systemsetting", {"q": key, "v": "custom:(value)"}
        )
        if status:
            return response["results"][0]["value"]
    except Exception as e:
        raise Exception(e)


def check_if_user_has_privilege(req, privilege_to_check, user_privileges):
    """
    Checks if a user has a specific privilege.

    Parameters:
        req (Request): The request object.
        privilege_to_check (str): The UUID of the privilege to check.
        user_privileges (list): A list of user privileges.

    Returns:
        bool: True if the user has the privilege, False otherwise.
    """
    # Check if user is admin grant all privileges
    if req.session["logged_user"]["user"]["systemId"] == "admin":
        return True
    has_privilege = False
    for privilege in user_privileges:
        if privilege["uuid"] == privilege_to_check:
            has_privilege = True
    return has_privilege


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
