"""
This file contains functions for interacting with the REST API.
It uses @handle_rest_exceptions decorator to handle any exceptions occured during the REST calls.
"""


import requests
import base64
from utilities import metadata_util as mu
from utilities import locations_util as lu
from mdrtb.settings import REST_API_BASE_URL
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
        cache.clear()
        req.session.flush()
        req.session.create()
        req.session["redirect_url"] = redirect_url
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
    if response.ok:
        logger.info(f"POST Request successful, status: {response.status_code}")
        return True, response.json()
    logger.info(f"'POST Request failed to /{endpoint}, status: {response.status_code}'")
    if "error" in response.json():
        logger.error(response.json(), exc_info=True)
        raise Exception(
            response.json()["error"]["message"].replace("[", "").replace("]", "")
        )
    response.raise_for_status()


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
