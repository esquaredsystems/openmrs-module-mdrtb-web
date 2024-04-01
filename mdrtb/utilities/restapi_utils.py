"""
This file contains functions for interacting with the REST API.
It uses @handle_rest_exceptions decorator to handle any exceptions occured during the REST calls.
"""


import requests
import base64
from utilities import metadata_util as mu
from utilities import locations_util as lu
from mdrtb.settings import REST_API_BASE_URL
from mdrtb.settings import QUALIS_API_BASE_URL
from django.contrib import messages
from django.core.cache import cache
from utilities.exceptions import handle_rest_exceptions
from urllib.parse import urlencode
import logging

logger = logging.getLogger("django")


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
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        if response.json()["authenticated"]:
            logger.info("User Authenticated")
            req.session["session_id"] = response.json()["sessionId"]
            if "user" in response.json():
                req.session["logged_user"] = response.json()
            req.session["encoded_credentials"] = encoded_credentials
            req.session["locale"] = response.json()["user"]["userProperties"][
                "defaultLocale"
            ]
            mu.get_all_concepts(req)
            lu.create_location_hierarchy(req)
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
            cache.clear()
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
    )
    logger.info(f"'Making GET call to /{endpoint}'")
    if response.status_code == 403:
        session_expired_msg = mu.get_global_msgs("require.login", source="OpenMRS")
        messages.info(req, session_expired_msg)
        logger.info("Session expired")
        clear_session(req)
        raise Exception(session_expired_msg)
    response.raise_for_status()
    logger.info(
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
        url=REST_API_BASE_URL + endpoint, headers=get_auth_headers(req), json=data
    )
    logger.info(f"'Making POST call to /{endpoint}'")
    response.raise_for_status()
    if response.ok:
        data = response.json()
        logger.info(f"POST Request successful, status: {response.status_code}")
        return True, data
    if response.status_code == 403:
        clear_session(req)
    logger.info(f"'POST Request failed to /{endpoint}, status: {response.status_code}'")
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
        url=REST_API_BASE_URL + endpoint, headers=get_auth_headers(req)
    )
    logger.info(f"'Making DELETE call to /{endpoint}'")
    response.raise_for_status()
    logger.info(
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
            "Cookie": "JSESSIONID={}".format(req.session["session_id"]),
        }
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
    encoded_credentials = base64.b64encode("username:password".encode("ascii")).decode("ascii")
    # Set the headers including Authorization with Basic Authentication
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    # Make a POST request to send Lab order data to QuaLIS
    logger.info(f"Making POST call to {url}")
    response = requests.post(url=url, headers={}, json=data)
    # Check for any errors
    response.raise_for_status()
    # If the response is successful, parse and return the response data
    if response.ok:
        # data = response.json()
        logger.info(f"POST Request successful, status: {response.status_code}")
        return response.status_code

    # Log and handle errors in the response JSON
    logger.info(f"POST Request failed to {url}, status: {response.status_code}")
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
