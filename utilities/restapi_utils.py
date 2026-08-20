"""
This file contains functions for interacting with the REST API.
It uses @handle_rest_exceptions decorator to handle any exceptions occured during the REST calls.
"""


import requests
import base64
from utilities import metadata_util as mu
from utilities import locations_util as lu
from settings.settings import REST_API_BASE_URL
from settings.settings import QUALIS_API_BASE_URL, QUALIS_API_CREDENTAILS
from settings.settings import REST_TIMEOUT
from django.contrib import messages
from utilities.exceptions import handle_rest_exceptions
from urllib.parse import urlencode
import logging

logger = logging.getLogger("django")

# Marker stored in session["session_id"] when OpenMRS gives us no JSESSIONID.
# Keeps the "logged in" checks truthy. See initiate_session().
BASIC_AUTH_ONLY = "basic-auth-only"


@handle_rest_exceptions
def initiate_session(req, username, password):
    """
    Initiates a session by sending an HTTP GET request to the /session endpoint.
    Parameters:
    - req (object): The request object representing the incoming HTTP request.
    - username (str): The username used for authentication.
    - password (str): The password used for authentication.
    Returns:
    - bool: True if the session is initiated successfully, False otherwise.
    Raises:
    - Exception: If the credentials are invalid or an error occurs during the session initiation.
    Example Usage:
        initiate_session(req, "john_doe", "password123")
    """
    encoded_credentials = base64.b64encode(
        f"{username}:{password}".encode("ascii")
    ).decode("ascii")
    url = REST_API_BASE_URL + "session"
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    response = requests.get(url, headers=headers, timeout=REST_TIMEOUT)
    if response.status_code == 200:
        if response.json()["authenticated"]:
            logger.debug("User Authenticated")
            # OpenMRS removed "sessionId" from the /session response body due to security vulnerability. The session token now only arrives as the JSESSIONID cookie
            session_id = response.json().get("sessionId") or response.cookies.get(
                "JSESSIONID"
            )
            if not session_id:
                # Every request also carries HTTP Basic credentials, which OpenMRS accepts on its own, so the user is genuinely logged in
                logger.info(
                    "No sessionId in body and no JSESSIONID cookie; "
                    "continuing with Basic auth only"
                )
                session_id = BASIC_AUTH_ONLY
            req.session["session_id"] = session_id
            if "user" in response.json():
                req.session["logged_user"] = response.json()
            req.session["encoded_credentials"] = encoded_credentials
            req.session["locale"] = response.json()["user"]["userProperties"].get(
                "defaultLocale", "ru"
            )
            mu.get_all_concepts(req)
            # Load the UI translations into Redis, the same way concepts are loaded.
            # Imported here rather than at module level because messages_util reaches back into this module to make the
            # REST call, and a top-level import would be circular.
            from utilities import messages_util as msg # CAUTION! DO NOT MOVE THIS IMPORT TO TOP
            msg.warm(req, req.session["locale"])

            try:
                lu.create_location_hierarchy(req)
            except Exception:
                pass
            # mu.get_all_attribute_types(req)
            return True
        else:
            logger.warning("Invalid credentials")
            raise Exception(
                mu.get_global_msgs("auth.password.invalid", source="OpenMRS")
            )
    else:
        logger.error(f"Status_code = {response.status_code}", exc_info=True)
        raise Exception(response.json()["error"]["message"])


def clear_session(req):
    """
    Clears any data associated with the session and creates a new session.
    """
    try:
        if req.path == "/logout":
            redirect_url = "/"
        else:
            query_params = req.session.get("redirect_query_params", {})
            redirect_url = (
                req.session.get("redirect_url")
                + "?"
                + urlencode(query_params, safe="-[]',")
                if query_params
                else req.session.get("redirect_url")
            )
        current_patient_program_flow = req.session.get(
            "current_patient_program_flow", None
        )
        req.session.flush()
        req.session.create()
        req.session["redirect_url"] = redirect_url
        req.session["current_patient_program_flow"] = current_patient_program_flow
        logger.info("Session cleared. New created")
    except KeyError as ke:
        logger.error(str(ke), exc_info=True)


def is_session_authenticated(req):
    """
    Probes the OpenMRS /session endpoint with the current credentials.
    Returns True only when OpenMRS is reachable AND reports authenticated=true.
    Never raises (no @handle_rest_exceptions on purpose) — callers use it to
    decide between "show error" and "redirect to login".
    """
    try:
        response = requests.get(
            url=REST_API_BASE_URL + "session",
            headers=get_auth_headers(req),
            timeout=REST_TIMEOUT,
        )
        return response.status_code == 200 and response.json().get(
            "authenticated", False
        )
    except Exception as e:
        logger.warning(f"Session probe failed: {e}")
        return False


def describe_error(method, response):
    """Turns a failed OpenMRS response into a message a human can act on.

    OpenMRS answers a rejected write with 400 and puts the actual reason in the
    body ("Unknown property", "required", the failing field, ...). Calling
    response.raise_for_status() throws that body away and the request only
    shows up as "400 Client Error", which is not enough to fix anything. So the
    body is logged in full and its message is what gets raised.

    Also used by utilities/rest_admin.py so both REST paths report errors the
    same way.
    """
    detail = (response.text or "")[:1500]
    message = f"OpenMRS returned {response.status_code}"
    try:
        body = response.json()
        error = body.get("error") or {}
        if error:
            message = error.get("message", message)
            parts = [
                ge.get("message")
                for ge in (error.get("globalErrors") or [])
                if ge.get("message")
            ]
            for field, errs in (error.get("fieldErrors") or {}).items():
                for err in errs:
                    parts.append(f"{field}: {err.get('message', '')}".strip())
            if parts:
                message = message + ": " + "; ".join(parts)
    except ValueError:
        message = f"OpenMRS returned {response.status_code}: {detail[:300]}"
    logger.error(f"{method} {response.url} -> {response.status_code}: {detail}")
    return message


@handle_rest_exceptions
def get(req, endpoint, parameters):
    """
    Sends an HTTP GET request to a REST API endpoint.
    Parameters:
    - req (object): The request object representing the incoming HTTP request.
    - endpoint (str): The endpoint of the REST API to send the GET request to.
    - parameters (dict): Optional parameters to include in the GET request.
    Returns:
    - tuple: A tuple containing a boolean indicating the success of the request (True if successful),
             and the JSON response from the endpoint.
    Raises:
    - Exception: If the session has expired, or if an error occurs during the GET request.
    Example Usage:
        get(request, "patients", {"name": "John Doe"})
    """
    response = requests.get(
        url=REST_API_BASE_URL + endpoint,
        headers=get_auth_headers(req),
        params=parameters,
        timeout=REST_TIMEOUT,
    )
    logger.debug(f"'Making GET call to /{endpoint}'")
    if response.status_code == 401:
        session_expired_msg = mu.get_global_msgs("require.login", source="OpenMRS")
        messages.info(req, session_expired_msg)
        logger.debug("Session expired")
        clear_session(req)
        raise Exception(session_expired_msg)
    if not response.ok:
        raise Exception(describe_error("GET", response))
    logger.debug(
        f"GET Request successful to /{endpoint}, status: {response.status_code}"
    )
    return True, response.json()


@handle_rest_exceptions
def post(req, endpoint, data):
    """
    Sends an HTTP POST request to a REST API endpoint.
    Parameters:
    - req (object): The request object representing the incoming HTTP request.
    - endpoint (str): The endpoint of the REST API to send the POST request to.
    - data (dict): The JSON data to include in the POST request body.
    Returns:
    - tuple: A tuple containing a boolean indicating the success of the request (True if successful),
             and the JSON response from the endpoint.
    Raises:
    - Exception: If an error occurs during the POST request, or if the response contains an error.
    Example Usage:
        post(request, "users", {"name": "John Doe", "email": "john@example.com"})
    """
    response = requests.post(
        url=REST_API_BASE_URL + endpoint,
        headers=get_auth_headers(req),
        json=data,
        timeout=REST_TIMEOUT,
    )
    logger.debug(f"'Making POST call to /{endpoint}'")
    if response.ok:
        data = response.json()
        logger.debug(f"POST Request successful, status: {response.status_code}")
        return True, data
    if response.status_code == 401:
        clear_session(req)
    # Do NOT call raise_for_status() here. It raises before the body is read,
    # and the body is the only place OpenMRS says what was actually wrong with
    # the payload.
    raise Exception(describe_error("POST", response))


@handle_rest_exceptions
def delete(req, endpoint):
    """
    Sends an HTTP DELETE request to a REST API endpoint.
    Parameters:
    - req (object): The request object representing the incoming HTTP request.
    - endpoint (str): The endpoint of the REST API to send the DELETE request to.
    Returns:
    - tuple: A tuple containing a boolean indicating the success of the request (True if successful),
             and the response object from the DELETE request.
    Raises:
    - Exception: If an error occurs during the DELETE request.
    Example Usage:
         delete(request, "users/1")
    """
    response = requests.delete(
        url=REST_API_BASE_URL + endpoint,
        headers=get_auth_headers(req),
        timeout=REST_TIMEOUT,
    )
    logger.debug(f"'Making DELETE call to /{endpoint}'")
    if not response.ok:
        if response.status_code == 401:
            clear_session(req)
        raise Exception(describe_error("DELETE", response))
    logger.debug(
        f"'DEL Request successful to /{endpoint}, status: {response.status_code}'"
    )
    return True, response


def get_auth_headers(req):
    """
    Retrieves the authentication headers for a given request.
    Parameters:
    - req (object): The request object representing the incoming HTTP request.
    Returns:
    - dict: A dictionary containing the authentication headers.
    Raises:
    - Exception: If the required session data is missing or expired.
    """
    try:
        headers = {
            "Authorization": "Basic {}".format(req.session["encoded_credentials"]),
        }
        session_id = req.session["session_id"]
        # Only send a real JSESSIONID. BASIC_AUTH_ONLY is our internal marker for
        # "OpenMRS issued no cookie" — sending it as a cookie would be a bogus
        # session token. Basic auth in the header authenticates the call anyway.
        if session_id and session_id != BASIC_AUTH_ONLY:
            headers["Cookie"] = "JSESSIONID={}".format(session_id)
        return headers
    except KeyError as ke:
        logger.error(ke, exc_info=True)
        clear_session(req)
        raise Exception(mu.get_global_msgs("auth.session.expired", source="OpenMRS"))


def post_lab_order(data):
    """
    Send a Lab order to QuaLIS (LIMS) via REST endpoints.
    Args:
        data (dict): The data object containing the Lab order information in the required format.
    Returns:
        bool: True if the Lab order is successfully posted to QuaLIS, False otherwise.
        dict: A dictionary containing the response data from QuaLIS if the request is successful.
    Raises:
        Exception: If there is an error during the request or if the response status code indicates an error.
            The exception message provides detailed information about the error.
    """
    # Construct the URL for the QuaLIS API endpoint
    url = QUALIS_API_BASE_URL + "externalorder/createExternalOrderOpenMrs"
    # Encode the credentials for Basic Authentication
    encoded_credentials = base64.b64encode(QUALIS_API_CREDENTAILS.encode("ascii")).decode("ascii")
    # Set the headers including Authorization with Basic Authentication
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    # Make a POST request to send Lab order data to QuaLIS
    logger.debug(f"Making POST call to {url}")
    response = requests.post(url=url, headers={}, json=data, timeout=REST_TIMEOUT)
    # Check for any errors
    response.raise_for_status()
    # If the response is successful, parse and return the response data
    if response.ok:
        # data = response.json()
        logger.debug(f"POST Request successful, status: {response.status_code}")
        return response.status_code

    # Log and handle errors in the response JSON
    logger.debug(f"POST Request failed to {url}, status: {response.status_code}")
    if "error" in response.json():
        logger.error(response.json(), exc_info=True)
        short_error_message = response.json()["error"]["message"]
        detailed_message = None
        if "globalErrors" in response.json()["error"]:
            detailed_message = response.json()["error"]["globalErrors"][0]["message"]
        error_message = (
            short_error_message + ": " + detailed_message
            if detailed_message
            else short_error_message
        )
        raise Exception(error_message)
