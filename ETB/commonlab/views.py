from email import header
from urllib import response
from django.shortcuts import render,redirect
import requests
from django.http import JsonResponse
from . import helpers


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
        headers = {'Authorization': f'Basic {req.session["encodedCredentials"]}' , 'Cookie' : f"JSESSIONID={req.session['sessionId']}"}
        response = requests.post(url,data=body,headers=headers)
        if response.status_code == 201:
            return redirect('managetesttypes')
        else:
            print('Error posting')
            print(response.status_code)
            print(response.json()['error']['message'])
    concepts = helpers.getConceptsByType(req,'labtesttype')
    context['referenceConcepts'] = concepts
    context['testGroups'] = testGroups
    return render(req,'commonlab/addtesttypes.html',context=context)


def editTestType(req,uuid):
    context = {}
    url = BASE_URL + f'commonlab/labtesttype/{uuid}?v=full'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        context['testType'] = {
            'uuid' : data['uuid'],
            'name' : data['name'],
            'testGroup' : data['testGroup'],
            'shortName' : data['shortName'],
            'requiresSpecimen' : data['requiresSpecimen'],
            'referenceConcept' : {
                'uuid' : data['referenceConcept']['uuid'],
                'name' : data['referenceConcept']['display']
            },
            'description' : data['description']
        }
        testGroupsCopy = testGroups.copy()
        testGroupsCopy.remove(testGroupsCopy[testGroupsCopy.index(data['testGroup'])])
        referenceConeptsCopy = referenceConepts.copy()
        referenceConeptsCopy.remove(referenceConeptsCopy[referenceConeptsCopy.index(data['referenceConcept']['display'])])
        context['state'] = 'edit'
        context['testGroups'] = testGroupsCopy
        context['referenceConcepts'] = referenceConeptsCopy
        return render(req,'commonlab/addtesttypes.html',context=context)
    else:
        return render(req,'commonlab/managetesttypes.html',context=context)



def manageAttributes(req):
    url = BASE_URL + 'commonlab/labtesttype'
    body={
        "name" : "Test from API",
        "testGroup" : testGroups[5],
        "referenceConcept" : 572,
        "requiresSpecimen" : True


    }
    response = requests.post(url=url,json=body)

    return render(req,'commonlab/manageattributes.html')


