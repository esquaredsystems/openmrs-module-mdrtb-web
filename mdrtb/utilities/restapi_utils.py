import requests
import base64
from utilities import metadata_util as mu
from mdrtb.settings import BASE_URL
from django.shortcuts import redirect
from django.contrib import messages, auth
from django.core.cache import cache


def initiate_session(req, username, password):
    try:
        cache.clear()
        encoded_credentials = base64.b64encode(
            f"{username}:{password}".encode('ascii')).decode('ascii')
        url = BASE_URL + 'session'
        headers = {'Authorization': f'Basic {encoded_credentials}'}
        print('MAKING RESPONSE')

        response = requests.get(url, headers=headers)
        print('RESPONSE', response)
        if response.status_code == 200 and response.json()['authenticated']:
            req.session['session_id'] = response.json()['sessionId']
            if 'user' in response.json():
                req.session['logged_user'] = response.json()['user']
            req.session['encoded_credentials'] = encoded_credentials
            req.session['locale'] = 'en'
            return True
        else:
            clear_session(req)
            messages.error(
                req, mu.get_global_msgs('auth.password.invalid', source='OpenMRS'))
    except Exception as e:
        print(e)
        messages.error(req, "Error loggin in. Please try again later")
        return False


def clear_session(req):
    try:
        cache.clear()
        auth.logout(req)
        del req.session['session_id']
        del req.session['encoded_credentials']
        del req.session['locale']
        del req.session['logged_user']
    except KeyError as e:
        pass


def get(req, endpoint, parameters):
    try:
        response = requests.get(
            url=BASE_URL+endpoint, headers=get_auth_headers(req), params=parameters)
        if response.status_code == 403:
            clear_session(req)
            messages.error(req, 'Your session has expired')
            raise Exception('Your session has expired')
        response.raise_for_status()
        return True, response.json()
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


def post(req, endpoint, data):
    try:
        response = requests.post(url=BASE_URL+endpoint,
                                 headers=get_auth_headers(req), json=data)
        if response.status_code == 201:
            return True, response.json()
    except Exception as e:
        print(e)
        raise Exception(response.json()['error']['message'])


def delete(req, endpoint):
    try:
        response = requests.delete(
            url=BASE_URL+endpoint, headers=get_auth_headers(req))
        response.raise_for_status()
        return True, response
    except Exception as e:
        raise Exception(str(e))


def get_auth_headers(req):
    headers = {'Authorization': 'Basic {}'.format(req.session["encoded_credentials"]),
               'Cookie': "JSESSIONID={}".format(req.session['session_id'])}
    return headers
