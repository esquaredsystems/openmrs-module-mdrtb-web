import requests
import base64
from utilities import metadata_util as mu
from mdrtb.settings import BASE_URL


def initiate_session(req, username, password):
    encoded_credentials = base64.b64encode(
        f"{username}:{password}".encode('ascii')).decode('ascii')
    url = BASE_URL + 'session'
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        req.session['session_id'] = response.json()['sessionId']
        req.session['logged_user'] = response.json()['user']
        req.session['encoded_credentials'] = encoded_credentials
        req.session['locale'] = 'en'
        return True
    else:
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
    # This will remove all the login info for user
    del req.session['session_id']
    
    del req.session['encoded_credentials']
    del req.session['locale']
    del req.session['logged_user']
    return None


def get(req, endpoint, parameters):
    response = requests.get(url=BASE_URL + endpoint,
                            headers=get_auth_headers(req), params=parameters)
    if response.status_code == 200:
        return True, response.json()
    elif response.status_code == 403:
        refreshed_session = refresh_session(req)
        return False, response.status_code


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
