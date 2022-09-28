from email import header
from urllib import response
from django.shortcuts import render
import requests
from django.http import JsonResponse


BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1/'


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




def managetesttypes(req):
    url = 'commonlab/labtesttype'
    response = requests.get(url=BASE_URL+url,params={'v' : 'default'})
    print(len(response.json()['results']))
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
        print(req.POST['testname'])
    
    print(req.session["encodedCredentials"])
    print(req.session['sessionId'])
    url = BASE_URL + 'commonlab/concept?type=labtesttype'
    headers = {'Authorization': f'Basic {req.session["encodedCredentials"]}' , 'Cookie' : f"JSESSIONID={req.session['sessionId']}"}
    print(headers)
    response = requests.get(url,headers=headers)
    print(response.json())
    context['testGroups'] = testGroups
    context['referenceConepts'] = referenceConepts

    return render(req,'commonlab/addtesttypes.html',context=context)


def editTestType(req,uuid):
    context = {}
    url = BASE_URL + f'commonlab/labtesttype/{uuid}?v=full'
    response = requests.get(url)
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
    context['state'] = 'edit'
    testGroupsCopy = testGroups.copy()
    testGroupsCopy.remove(testGroupsCopy[testGroupsCopy.index(data['testGroup'])])
    referenceConeptsCopy = referenceConepts.copy()
    referenceConeptsCopy.remove(referenceConeptsCopy[referenceConeptsCopy.index(data['referenceConcept']['display'])])
    context['testGroups'] = testGroupsCopy
    context['referenceConepts'] = referenceConeptsCopy

    
    return render(req,'commonlab/addtesttypes.html',context=context)