from multiprocessing import reduction
from django.shortcuts import render,redirect
import requests
from django.http import JsonResponse
import base64


BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1/'





def index(req):
    return render(req,'tbregister/base.html')

def login(req):
    if req.method == 'POST':
        url = BASE_URL+'/session'
        username = req.POST['username']
        password = req.POST['password']
        encoded_credentials = base64.b64encode(f"{username}:{password}".encode('ascii')).decode('ascii')
        headers = {'Authorization': f'Basic {encoded_credentials}'}
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            req.session['sessionId'] = response.json()['sessionId']
            req.session['encodedCredentials'] = encoded_credentials
            return render(req,'tbregister/base.html')
    return render(req,'tbregister/login.html')

def enroll(req):
    return render(req,'tbregister/enroll_with_form.html')

    
def enroll_two(req):
    return render(req,'tbregister/enroll_without_form.html')

def actual_enroll(req):
    return render(req,'tbregister/actual_enroll_form.html')


def logout(req):
    encoded_credentials = req.session['encodedCredentials']
    headers = {'Authorization': f'Basic {encoded_credentials}' , 'Cookie' : f"JSESSIONID={req.session['sessionId']}"}
    response = requests.delete(f'{BASE_URL}/session', headers=headers)
    print(response.status_code)
    if response.status_code == 204:
        if 'sessionId' in req.session:
            del req.session['sessionId']
    return redirect('home')