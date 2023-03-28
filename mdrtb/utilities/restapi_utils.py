import requests
import base64
from utilities import metadata_util as mu
from mdrtb.settings import REST_API_BASE_URL
from django.contrib import messages
from django.core.cache import cache
from utilities.exceptions import handle_rest_exceptions
from urllib.parse import urlencode
import logging

logger = logging.getLogger("django")


@handle_rest_exceptions
def initiate_session(req, username, password):
    encoded_credentials = base64.b64encode(
        f"{username}:{password}".encode("ascii")
    ).decode("ascii")
    print(encoded_credentials)
    url = REST_API_BASE_URL + "session"
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    response = requests.get(url, headers=headers)
    print(response.json())
    if response.status_code == 200:
        if response.json()["authenticated"]:
            logger.info("User Authenticated")
            req.session["session_id"] = response.json()["sessionId"]
            if "user" in response.json():
                req.session["logged_user"] = response.json()["user"]
            req.session["encoded_credentials"] = encoded_credentials
            req.session["locale"] = response.json()["locale"]
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
    try:
        query_params = req.session.get("redirect_query_params", {})
        redirect_url = (
            req.session.get("redirect_url")
            + "?"
            + urlencode(query_params, safe="-[]',")
            if query_params
            else req.session.get("redirect_url")
            if req.path != "/logout"
            else "/"
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
    response = requests.get(
        url=REST_API_BASE_URL + endpoint,
        headers=get_auth_headers(req),
        params=parameters,
    )
    logger.info(f"'Making GET call to /{endpoint}'")
    if response.status_code == 403:
        session_expired_msg = mu.get_global_msgs(
            "require.login", source="OpenMRS"
        )
        logger.info("Session expired")
        clear_session(req)
        messages.info(req, session_expired_msg)
        raise Exception(session_expired_msg)
    response.raise_for_status()
    logger.info(
        f"'GET Request successful to /{endpoint}, status: {response.status_code}'"
    )
    return True, response.json()


@handle_rest_exceptions
def post(req, endpoint, data):
    response = requests.post(
        url=REST_API_BASE_URL + endpoint, headers=get_auth_headers(req), json=data
    )
    logger.info(f"'Making POST call to /{endpoint}'")
    if response.ok:
        logger.info(f"POST Request successful, status: {response.status_code}")
        return True, response.json()
    logger.info(f"'POST Request failed to /{endpoint}, status: {response.status_code}'")
    raise Exception(response.json()["error"]["message"])


@handle_rest_exceptions
def delete(req, endpoint):
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
