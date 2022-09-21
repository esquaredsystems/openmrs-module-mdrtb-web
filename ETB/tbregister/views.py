from urllib import response
from django.shortcuts import render
import requests


# Create your views here.

BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1/'

def index(req):
    return render(req,'tbregister/base.html')

def login(req):
    return render(req,'tbregister/login.html')

def enroll(req):
    return render(req,'tbregister/enroll_with_form.html')

    
def enroll_two(req):
    return render(req,'tbregister/enroll_without_form.html')

def actual_enroll(req):
    return render(req,'tbregister/actual_enroll_form.html')


def commonlab(req):
    url = 'commonlab/labtesttype'
    response = requests.get(url=BASE_URL+url,params={'v' : 'default'})
    
    context = {
        'response' : response.json()['results'] 
    }
    return render(req,'tbregister/commonlab.html',context=context)