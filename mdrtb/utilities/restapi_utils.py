import requests
import base64
from utilities import metadata_util as mu
from mdrtb.settings import REST_API_BASE_URL
from django.contrib import messages
from django.core.cache import cache
from utilities.exceptions import handle_rest_exceptions
from urllib.parse import urlencode


@handle_rest_exceptions
def initiate_session(req, username, password):
    encoded_credentials = base64.b64encode(
        f"{username}:{password}".encode('ascii')).decode('ascii')
    url = REST_API_BASE_URL + 'session'
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    if response.status_code == 200 and response.json()['authenticated']:
        req.session['session_id'] = response.json()['sessionId']
        if 'user' in response.json():
            req.session['logged_user'] = response.json()['user']
        req.session['encoded_credentials'] = encoded_credentials
        req.session['locale'] = response.json()['locale']
        return True
    else:
        clear_session(req)
        raise Exception(mu.get_global_msgs(
            'auth.password.invalid', source='OpenMRS'))


def clear_session(req):
    try:
        query_params = req.session.get('redirect_query_params', {})
        redirect_url = '/' if req.path == '/logout' else req.session.get(
            'redirect_url') + '?' + urlencode(query_params, safe="-[]',") if query_params else req.session.get('redirect_url')
        cache.clear()
        req.session.flush()
        req.session.create()
        req.session['redirect_url'] = redirect_url
    except KeyError:
        pass


@handle_rest_exceptions
def get(req, endpoint, parameters):
    response = requests.get(
        url=REST_API_BASE_URL+endpoint, headers=get_auth_headers(req), params=parameters)
    if response.status_code == 403:
        clear_session(req)
        session_expired_msg = mu.get_global_msgs(
            'auth.session.expired', source='OpenMRS')
        messages.error(req, session_expired_msg)
        raise Exception(session_expired_msg)
    response.raise_for_status()
    return True, response.json()


@handle_rest_exceptions
def post(req, endpoint, data):
    response = requests.post(url=REST_API_BASE_URL+endpoint,
                             headers=get_auth_headers(req), json=data)
    response.raise_for_status()
    print(f'STATUS CODE FOR {endpoint} is {response.status_code}')
    if response.ok:
        return True, response.json()
    return False, response.json()


@handle_rest_exceptions
def delete(req, endpoint):
    response = requests.delete(
        url=REST_API_BASE_URL+endpoint, headers=get_auth_headers(req))
    response.raise_for_status()
    return True, response


def get_auth_headers(req):
    try:
        headers = {'Authorization': 'Basic {}'.format(req.session["encoded_credentials"]),
                   'Cookie': "JSESSIONID={}".format(req.session['session_id'])}
        return headers
    except KeyError:
        clear_session(req)
        raise Exception(mu.get_global_msgs(
            'auth.session.expired', source='OpenMRS'))
