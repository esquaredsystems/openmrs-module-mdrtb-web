from http.client import HTTPException
import requests
from django.http import JsonResponse
from mdrtb.settings import BASE_URL
import base64



def initiate_session(req,credentials):
    encoded_credentials = base64.b64encode(credentials.encode('ascii')).decode('ascii')
    url = BASE_URL + '/session'
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        req.session['sessionId'] = response.json()['sessionId']
        req.session['encodedCredentials'] = encoded_credentials
        return True
    else:
        return False
    

def get(req, endpoint, parameters):
    response = requests.get(url=BASE_URL + endpoint,headers=get_auth_headers(req),params=parameters)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.json()


def get_auth_headers(req):
    headers = {'Authorization': f'Basic {req.session["encodedCredentials"]}',
               'Cookie': f"JSESSIONID={req.session['sessionId']}"}
    return headers





