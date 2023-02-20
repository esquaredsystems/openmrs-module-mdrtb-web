import requests
import base64
from utilities import metadata_util as mu
from mdrtb.settings import REST_API_BASE_URL
from django.shortcuts import redirect
from django.contrib import messages, auth
from django.core.cache import cache


def initiate_session(req, username, password):
    try:
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
    except requests.exceptions.HTTPError as httperr:
        print(httperr)
        raise Exception(
            "An error occured while processing your request. Please try again later")
    except requests.exceptions.ConnectionError as connection_err:
        print(connection_err)
        raise Exception('Please check your internet connection and try again')
    except requests.exceptions.RequestException as err:
        print(err)
        raise Exception(
            'An error occured while processing your request. Please try again later')


def clear_session(req):
    try:
        cache.clear()
        auth.logout(req)
        req.session.flush()
    except KeyError:
        pass


def get(req, endpoint, parameters):
    try:
        response = requests.get(
            url=REST_API_BASE_URL+endpoint, headers=get_auth_headers(req), params=parameters)
        if response.status_code == 403:
            redirect_url = req.session['redirect_url']
            clear_session(req)
            raise Exception(mu.get_global_msgs(
                'auth.session.expired', source='OpenMRS'), redirect_url)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.HTTPError as httperr:
        print(httperr)
        raise Exception(
            "An error occured while processing your request. Please try again later")
    except requests.exceptions.ConnectionError as connection_err:
        print(connection_err)
        raise Exception('Please check your internet connection and try again')
    except requests.exceptions.RequestException as err:
        print(err)
        raise Exception(
            'An error occured while processing your request. Please try again later')


def post(req, endpoint, data):
    try:
        response = requests.post(url=REST_API_BASE_URL+endpoint,
                                 headers=get_auth_headers(req), json=data)
        if response.ok:
            return True, response.json()
        response.raise_for_status()
    except requests.exceptions.HTTPError as httperr:
        print(httperr)
        raise Exception(
            "An error occured while processing your request. Please try again later")
    except requests.exceptions.RequestException as err:
        print(err)
        raise Exception(
            'An error occured while processing your request. Please try again later')
    except requests.exceptions.ConnectionError as connection_err:
        print(connection_err)
        raise Exception('Please check your internet connection and try again')


def delete(req, endpoint):
    try:
        response = requests.delete(
            url=REST_API_BASE_URL+endpoint, headers=get_auth_headers(req))
        response.raise_for_status()
        return True, response
    except Exception as e:
        raise Exception(str(e))


def get_auth_headers(req):
    headers = {'Authorization': 'Basic {}'.format(req.session["encoded_credentials"]),
               'Cookie': "JSESSIONID={}".format(req.session['session_id'])}
    return headers
