import requests
import base64
from utilities import metadata_util as mu
from mdrtb.settings import BASE_URL
from django.shortcuts import redirect
from django.contrib import messages, auth
from django.core.cache import cache


def initiate_session(req, username, password):
    cache.clear()
    encoded_credentials = base64.b64encode(
        f"{username}:{password}".encode('ascii')).decode('ascii')
    url = BASE_URL + 'session'
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    response = requests.get(url, headers=headers)
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
            req, mu.get_global_msgs('auth.password.invalid'))
        return False


def refresh_session(req):
    response = requests.get(url=BASE_URL + 'session')
    if response.status_code == 200:
        req.session['session_id'] = response.json()['sessionId']
        req.session['logged_user'] = response.json()['user']
        req.session['encoded_credentials'] = encoded_credentials
        req.session['locale'] = 'en'
        return True
    else:
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
    finally:
        return None


def get(req, endpoint, parameters):
    try:
        response = requests.get(
            url=BASE_URL+endpoint, headers=get_auth_headers(req), params=parameters)
        if response:
            print('we got response with status {}'.format(response.status_code))
            if response.status_code == 200:
                return True, response.json()
            else:
                print(response.status_code)
                return False, response.json()['error']
    except Exception as e:
        print(e)
        print('RESPONSE', response)
        return False, None


# def get(req, endpoint, parameters):
#     print('WE HERE AT GET')
#     try:
#         response = requests.get(url=BASE_URL + endpoint,
#                             headers=get_auth_headers(req), params=parameters)
#         if response:
#             print('we got response with status {}'.format(response.status_code))
#             if response.status_code == 200:
#                 print('200')
#                 return True, response.json()
#             elif response.status_code == 403:
#                 print('Expired')
#                 clear_session(req)
#                 messages.error(req, 'Please Login again')
#                 return False, redirect('home')
#             else:
#                 print('Failed')
#                 print(response.status_code)
#                 return False, response.status_code
#         else:
#             print('NO RESPONSE')
#             messages.error(req, 'Error logging in')
#             clear_session(req)
#             return False, redirect('home')
#     except Exception as e:
#         print('EXCEPTION')
#         messages.error(req, 'Error logging in')
#         return False, redirect('home')
#         print(e)


def post(req, endpoint, data):
    response = requests.post(url=BASE_URL+endpoint,
                             headers=get_auth_headers(req), json=data)
    if response.status_code == 201:
        return True, response.json()
    return False, response.json()


def delete(req, endpoint):
    response = requests.delete(
        url=BASE_URL+endpoint, headers=get_auth_headers(req))
    print(BASE_URL+endpoint)
    if response.ok:
        return True, response
    else:
        return False, response


def get_auth_headers(req):
    headers = {'Authorization': f'Basic {req.session["encoded_credentials"]}',
               'Cookie': f"JSESSIONID={req.session['session_id']}"}
    return headers
