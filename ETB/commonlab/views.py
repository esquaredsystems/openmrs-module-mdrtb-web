from django.shortcuts import render,redirect
import requests
from django.http import JsonResponse
from . import helpers
import json

BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1/'



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


def managetesttypes(req):
    url = 'commonlab/labtesttype'
    response = requests.get(url=BASE_URL+url,params={'v' : 'default'})
    context = {
        'response' : response.json()['results']
    }
    return render(req,'commonlab/managetesttypes.html',context=context)


def fetchAttributes(req) :
    response  = helpers.getAttributesByLabTest(req.GET['uuid'])
    attributes  = []
    for attr in response:
        attributes.append({
            'attrName' : attr['name'],
            'sortWeight' : attr['sortWeight'],
            'groupName' : attr['groupName'],
            'multisetName' : attr['multisetName']
        })



    return JsonResponse({'attributes' : attributes})



def addTestTypes(req):
    context = {}
    if req.method == 'POST':
        body = {
        "name" : req.POST['testname'],
        "testGroup" : req.POST['testgroup'],
        "requiresSpecimen": True if req.POST['requirespecimen'] == 'Yes' else False,
        "referenceConcept" : req.POST['referenceconcept'],
        "description" :req.POST['description'],
        "shortName" : None if req.POST['shortname'] == '' else req.POST['shortname'],
        }
        url = BASE_URL + 'commonlab/labtesttype'
        response = helpers.addOrEditTestType(req,body,url)
        if response.status_code == 201:
            return redirect('managetesttypes')
        else:
            print('Error posting')
            print(response.status_code)
            print(response.json()['error']['message'])
            context['error'] = response.json()['error']['message']
            return render(req,'commonlab/addtesttypes.html',context=context)
    concepts = helpers.getConceptsByType(req,'labtesttype')
    context['referenceConcepts'] = concepts
    context['testGroups'] = testGroups
    return render(req,'commonlab/addtesttypes.html',context=context)


def editTestType(req,uuid):
    url = BASE_URL + f'commonlab/labtesttype/{uuid}?v=full'
    headers = {'Authorization': f'Basic {req.session["encodedCredentials"]}' , 'Cookie' : f"JSESSIONID={req.session['sessionId']}"}
    response = requests.get(url,headers=headers)
    data = response.json()
    context = {'state' : 'edit'}
    context['testType'] = {
        'uuid'  : data['uuid'],
        'name' : data['name'],
        'shortName' : data['shortName'],
        'testGroup' : data['testGroup'],
        'requiresSpecimen' : data['requiresSpecimen'],
        'description' : data['description'],
        'referenceConcept' : {
            'uuid' : data['referenceConcept']['uuid'],
            'name' :  data['referenceConcept']['display'],
        }
    }
    context['referenceConcepts'] = helpers.getConceptsByType(req,'labtesttype')
    context['testGroups'] = helpers.removeDuplicatesGroup(testGroups,data['testGroup'])
    if req.method == 'POST':
        body = {
        "name" : req.POST['testname'],
        "testGroup" : req.POST['testgroup'],
        "requiresSpecimen": True if req.POST['requirespecimen'] == 'Yes' else False,
        "referenceConcept" : req.POST['referenceconcept'],
        "description" :req.POST['description'],
        "shortName" : None if req.POST['shortname'] == '' else req.POST['shortname'],
        }
        url = BASE_URL + f'commonlab/labtesttype/{uuid}'
        response = helpers.addOrEditTestType(req,body,url)
        if response.status_code == 200:
            return redirect('managetesttypes')


    return render(req,'commonlab/addtesttypes.html',context=context)
    



def manageAttributes(req,uuid):
    context = {}
    response = helpers.getAttributesByLabTest(uuid)
    print(response)
    context['attributes'] = response
    
    return render(req,'commonlab/manageattributes.html',context=context)


def addattributes(req):
    return render(req,'commonlab/addattributes.html')


def managetestorders(req):
    return render(req,'commonlab/managetestorders.html')

def managetestsamples(req,uuid):
    return render(req,'commonlab/managetestsamples.html')