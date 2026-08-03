"""
Shared REST plumbing for the Administration screens (locations, users, ...).

Exists for two reasons that were learned the hard way against this server:

1. restapi_utils.get/post call raise_for_status() and the exception decorator
   replaces the result with a generic "an error occurred" message, so the actual
   OpenMRS error text never reaches the log or the user. The helpers here
   surface the real response body, which is what made the location 500s
   diagnosable.

2. OpenMRS caps page size with the global property
   webservices.rest.maxResultsAbsolute (100 on this deployment). A larger limit
   does NOT clamp — it returns HTTP 500 "Administrator has set absolute limit
   at 100". Every list endpoint must therefore be paged, never fetched with a
   big limit.
"""

import logging
import re

import requests

import utilities.restapi_utils as ru
from settings.settings import REST_API_BASE_URL, REST_TIMEOUT

logger = logging.getLogger("django")

# Never raise above the server cap; page instead. get_all_pages() lowers this
# automatically if a server reports a smaller cap.
DEFAULT_PAGE_SIZE = 100

# Safety valve: a server that kept returning full pages would otherwise loop
# forever and wedge the worker. 200 x 100 = 20,000 rows.
MAX_PAGES = 200

_ABSOLUTE_LIMIT_RE = re.compile(r"absolute limit at (\d+)")


class SessionExpired(Exception):
    """Raised when OpenMRS rejects our credentials so the view can redirect to login."""


def _request(method, req, endpoint, params=None, payload=None):
    url = REST_API_BASE_URL + endpoint
    headers = ru.get_auth_headers(req)
    try:
        if method == "GET":
            response = requests.get(
                url=url, headers=headers, params=params, timeout=REST_TIMEOUT
            )
        elif method == "POST":
            response = requests.post(
                url=url, headers=headers, json=payload, timeout=REST_TIMEOUT
            )
        else:
            response = requests.delete(url=url, headers=headers, timeout=REST_TIMEOUT)
    except requests.exceptions.RequestException as err:
        logger.error(f"{method} {endpoint} failed: {err}", exc_info=True)
        raise Exception(
            "Could not reach OpenMRS. Please check the connection and try again."
        )

    if response.status_code == 401:
        logger.warning(f"{method} {endpoint} -> 401, clearing session")
        ru.clear_session(req)
        raise SessionExpired()

    if response.ok:
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return None

    raise Exception(_describe_error(method, response))


def _describe_error(method, response):
    """Pulls the human-readable message out of an OpenMRS error body."""
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


def rest_get(req, endpoint, params=None):
    return _request("GET", req, endpoint, params=params)


def rest_post(req, endpoint, payload):
    return _request("POST", req, endpoint, payload=payload)


def rest_delete(req, endpoint):
    return _request("DELETE", req, endpoint)


def get_all_pages(req, endpoint, params=None):
    """
    Fetches every page of a list endpoint and returns the concatenated results.

    Always pages at DEFAULT_PAGE_SIZE because the server rejects (rather than
    clamps) an oversized limit. If a server reports a smaller cap, the error
    names it and we retry that page at the smaller size.
    """
    params = dict(params or {})
    page_size = DEFAULT_PAGE_SIZE
    results = []
    start_index = 0

    for _ in range(MAX_PAGES):
        page_params = dict(params, limit=page_size, startIndex=start_index)
        try:
            body = rest_get(req, endpoint, page_params)
        except SessionExpired:
            raise
        except Exception as e:
            match = _ABSOLUTE_LIMIT_RE.search(str(e))
            if match and int(match.group(1)) < page_size:
                page_size = int(match.group(1))
                logger.warning(
                    f"{endpoint}: server caps page size at {page_size}; retrying."
                )
                continue
            raise

        page = (body or {}).get("results", [])
        results.extend(page)
        if len(page) < page_size:
            return results
        start_index += page_size

    logger.warning(
        f"{endpoint}: stopped after {MAX_PAGES} pages ({len(results)} rows). "
        "The list may be truncated."
    )
    return results
