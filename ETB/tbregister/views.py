from inspect import Attribute
from re import U
from urllib import response
from django.shortcuts import render,redirect
import requests
from django.http import JsonResponse


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


def managetesttypes(req):
    url = 'commonlab/labtesttype'
    response = requests.get(url=BASE_URL+url,params={'v' : 'default'})
    print(len(response.json()['results']))
    context = {
        'response' : response.json()['results']
    }
    return render(req,'tbregister/commonlab/managetesttypes.html',context=context)


def fetchAttributes(req):
    url = BASE_URL + 'commonlab/labtestattributetype'
    params = {'testTypeUuid' : req.GET['uuid'],'v' : 'full'}
    response = requests.get(url=url,params=params)
    attributes  = []
    for attr in response.json()['results']:
        attributes.append({
            'attrName' : attr['name'],
            'sortWeight' : attr['sortWeight'],
            'groupName' : attr['groupName'],
            'multisetName' : attr['multisetName']
        })



    return JsonResponse({'attributes' : attributes})



def addtesttypes(req):
    context = {}
    # if req.GET['state'] == 'edit'
    if req.method == 'POST':
        print(req.POST['testname'])
    referenceConepts = [
        'MICROSCOPY TEST CONSTRUCT',
        'TUBERCULOSIS CULTURE CONSTRUCT',
        'L-J RESULT TEMPLATE',
        'HAIN 2 TEST CONSTRUCT',
        'MGIT RESULT TEMPLATE',
        'DST2 MGIT CONSTRUCT',
        'DST1 MGIT CONSTRUCT',
        'DST1 LJ CONSTRUCT',
        'CONTAMINATED TUBES RESULT TEMPLATE'
    ]
    testGroups = [
        'SEROLOGY',
        'CARDIOLOGY',
        'OPHTHALMOLOGY',
        'BACTERIOLOGY',
        'BIOCHEMISTRY',
        'BLOOD_BANK',
        'CYTOLOGY',
        'HEMATOLOGY',
        'IMMUNOLOGY',
        'MICROBIOLOGY',
        'RADIOLOGY',
        'SONOLOGY',
        'URINALYSIS',
        'OTHER'
    ]
    context['testGroups'] = testGroups
    context['referenceConepts'] = referenceConepts

    return render(req,'tbregister/commonlab/addtesttypes.html',context=context)