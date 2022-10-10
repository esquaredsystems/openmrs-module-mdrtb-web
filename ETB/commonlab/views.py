from urllib import response
from django.shortcuts import render,redirect
import requests
from django.http import JsonResponse
from . import helpers
import json

BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1/commonlab'



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

attributesDataTypes = [
    {
        'value' : 'org.openmrs.customdatatype.datatype.DateDatatype.name',
        'name' : 'Date'
    },
    {
        'value' : 'org.openmrs.customdatatype.datatype.BooleanDatatype.name',
        'name' : 'Boolean'
    },
    {
        'value' : 'org.openmrs.customdatatype.datatype.LongFreeTextDatatype.name',
        'name' : 'LongFreeText'
    },
    {
        'value' : 'org.openmrs.customdatatype.datatype.FreeTextDatatype.name',
        'name' : 'FreeText'
    },
    {
        'value' : 'org.openmrs.customdatatype.datatype.RegexValidatedTextDatatype.name',
        'name' : 'RegexValidatedText'
    },
    {
        'value' : 'org.openmrs.customdatatype.datatype.ConceptDatatype.name',
        'name' : 'Concept'
    },
    


    
    
    
    
    
]

attributesPrefferedHandler = [
    {
        'value' : 'org.openmrs.web.attribute.handler.DateFieldGenDatatypeHandler',
        'name' : 'DateFieldGenDatatype'
    },
    {
        'value' : 'org.openmrs.web.attribute.handler.LongFreeTextFileUploadHandler',
        'name' : 'LongFreeTextFileUpload'
    },
    {
        'value' : 'org.openmrs.web.attribute.handler.BooleanFieldGenDatatypeHandler',
        'name' : 'BooleanFieldGenDatatype'
    },
    {
        'value' : 'org.openmrs.web.attribute.handler.LongFreeTextTextareaHandler',
        'name' : 'LongFreeTextTextarea'
    },
    
    
    
    
    
    
    
    
]

def managetesttypes(req):
    url = '/labtesttype'
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
        url = BASE_URL + '/labtesttype'
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
    url = BASE_URL + f'/labtesttype/{uuid}?v=full'
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
    context['testGroups'] = helpers.removeGivenStrFromArr(testGroups,data['testGroup'])
    if req.method == 'POST':
        body = {
        "name" : req.POST['testname'],
        "testGroup" : req.POST['testgroup'],
        "requiresSpecimen": True if req.POST['requirespecimen'] == 'Yes' else False,
        "referenceConcept" : req.POST['referenceconcept'],
        "description" :req.POST['description'],
        "shortName" : None if req.POST['shortname'] == '' else req.POST['shortname'],
        }
        url = BASE_URL + f'/labtesttype/{uuid}'
        response = helpers.addOrEditTestType(req,body,url)
        if response.status_code == 200:
            return redirect('managetesttypes')


    return render(req,'commonlab/addtesttypes.html',context=context)
    

def retireTestType(req,uuid):
    if req.method == 'POST':
        url = BASE_URL + f'/labtesttype/{uuid}'
        headers = helpers.getAuthHeaders(req)
        response = requests.delete(url,headers=headers)
        if response.status_code == 204:
            return redirect('managetesttypes')
    return render(req,'commonlab/addtesttypes.html')

def manageAttributes(req,uuid):
    context = {'labTestUuid' : uuid}
    response = helpers.getAttributesByLabTest(uuid)
    context['attributes'] = response
    
    
    return render(req,'commonlab/manageattributes.html',context=context)


def addattributes(req,uuid):
    context = {'labTestUuid' : uuid,'prefferedHandlers' : attributesPrefferedHandler,'dataTypes' : attributesDataTypes}
    if req.method == 'POST':
        body= {
            'labTestType' : uuid,
            'name' : req.POST['name'],
            'description' : req.POST['desc'],
            'datatypeClassname' : req.POST['datatype'],
            'sortWeight' : float(int(req.POST.get('sortweight', 0.0))),
            'maxOccurs' : 0 if req.POST.get('maxoccur') == '' else req.POST.get('maxoccur'),
            'datatypeConfig' : req.POST.get('datatypeconfig', ''),
            'preferredHandlerClassname' : req.POST.get('handler', ''),
            'groupName' : req.POST.get('grpname', ''),
            'multisetName' : req.POST.get('mutname', ''),
            'handlerConfig' : req.POST.get('handleconfig', ''),

        }
        
        url = BASE_URL + '/labtestattributetype'
        headers = helpers.getAuthHeaders(req)
        response = requests.post(url,json=body,headers=headers)
        if response.status_code == 201:
            return redirect(f'/commonlab/manageattributes/{uuid}')
        else:
            print(response.status_code)
            print(response.json())
    
        
    return render(req,'commonlab/addattributes.html',context=context)


def editAttribute(req,uuid):
    context = {'state' : 'edit' ,}
    url = BASE_URL + f'/labtestattributetype/{uuid}?v=full'
    headers =helpers.getAuthHeaders(req)
    response = requests.get(url,headers=headers)
    context['attribute'] = helpers.customAttr(response.json(),attributesDataTypes,response.json()['datatypeClassname'],attributesPrefferedHandler,response.json()['preferredHandlerClassname'])
    context['dataTypes'] = helpers.removeGivenStrFromObjArr(attributesDataTypes,response.json()['datatypeClassname'],'views')
    context['prefferedHandlers'] = helpers.removeGivenStrFromObjArr(attributesPrefferedHandler,response.json()['preferredHandlerClassname'],'views')
    if req.method == 'POST':
        body= {
            'name' : req.POST['name'],
            'description' : req.POST['desc'],
            'datatypeClassname' : req.POST['datatype'],
            'sortWeight' : req.POST.get('sortweight', 0.0),
            'maxOccurs' : 0 if req.POST.get('maxoccur') == '' else req.POST.get('maxoccur'),
            'datatypeConfig' : req.POST.get('datatypeconfig', ''),
            'preferredHandlerClassname' : req.POST.get('handler', ''),
            'groupName' : req.POST.get('grpname', ''),
            'multisetName' : req.POST.get('mutname', ''),
            'handlerConfig' : req.POST.get('handleconfig', ''),

        }
        url = BASE_URL + f'/labtestattributetype/{uuid}'
        headers = helpers.getAuthHeaders(req)
        response = requests.post(url,json=body,headers=headers)
        if response.status_code == 200:
            return redirect(f'/commonlab')
        else:
            print(response.status_code)
            print(response.json())
            
    return render(req,'commonlab/addattributes.html',context=context)


def managetestorders(req):
    return render(req,'commonlab/managetestorders.html')

def managetestsamples(req,uuid):
    return render(req,'commonlab/managetestsamples.html')