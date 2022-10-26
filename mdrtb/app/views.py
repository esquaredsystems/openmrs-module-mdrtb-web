from os import stat
from django.shortcuts import render, redirect
import requests
from django.http import JsonResponse
import base64
import restapi_utils as ru
import commonlab_util as cu


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




def index(req):
    return render(req, 'app/app/tbregister/reportmockup.html')


def login(req):
    if 'sessionId' in req.session:
        return render(req, 'app/tbregister/enroll_without_form.html')
    else:
        if req.method == 'POST':
            username = req.POST['username']
            password = req.POST['password']
            response = ru.initiate_session(req,f"{username}:{password}")
            if response:
                return render(req, 'app/tbregister/enroll_without_form.html')
            else:
                context = {'error': response.status_code}
                return render(req, 'app/tbregister/login.html', context=context)
        else:
            return render(req, 'app/tbregister/login.html')


def search_patients(req):
    q = req.GET['q']
    _ , response = ru.get(req,'patient',{'q':q , 'v':'full'})
    return JsonResponse(response)


def enroll(req):
    return render(req, 'app/tbregister/enroll_with_form.html')


def enroll_two(req):
    return render(req, 'app/tbregister/enroll_without_form.html')


def actual_enroll(req):
    return render(req, 'app/tbregister/actual_enroll_form.html')


def patientList(req):
    context = {
        'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December'],
        'quaters': ['1', '2', '3', '4']

    }
    return render(req, 'app/tbregister/patientlist.html', context=context)


def patient_dashboard(req, uuid):
    return render(req, 'app/tbregister/dashboard.html')


def logout(req):
    encoded_credentials = req.session['encodedCredentials']
    headers = {'Authorization': f'Basic {encoded_credentials}', 'Cookie': f"JSESSIONID={req.session['sessionId']}"}
    response = requests.delete(f'{BASE_URL}/session', headers=headers)
    if response.status_code == 204:
        if 'sessionId' in req.session:
            del req.session['sessionId']
    return redirect('home')


def manage_test_types(req):
    status,response = ru.get(req,'commonlab/labtesttype',{'v' : 'default'})
    context = {'response' :response['results'] if status else []}
    return render(req,'app/commonlab/managetesttypes.html',context=context)


def fetch_attributes(req):
    response  = cu.get_attributes_of_labtest(req,req.GET['uuid'])
    attributes  = []
    for attribute in response:
        attributes.append({
            'attrName' : attribute['name'],
            'sortWeight' : attribute['sortWeight'],
            'groupName' : attribute['groupName'],
            'multisetName' : attribute['multisetName']
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
        response = ru.addOrEditTestType(req,body,url)
        if response.status_code == 201:
            return redirect('managetesttypes')
        else:
            print('Error posting')
            print(response.status_code)
            print(response.json()['error']['message'])
            context['error'] = response.json()['error']['message']
            return render(req,'app/commonlab/addtesttypes.html',context=context)
    concepts = ru.getConceptsByType(req,'labtesttype')
    context['referenceConcepts'] = concepts
    context['testGroups'] = testGroups
    return render(req,'app/commonlab/addtesttypes.html',context=context)


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
    context['referenceConcepts'] = ru.getConceptsByType(req,'labtesttype')
    context['testGroups'] = ru.removeGivenStrFromArr(testGroups,data['testGroup'])
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
        response = ru.addOrEditTestType(req,body,url)
        if response.status_code == 200:
            return redirect('managetesttypes')


    return render(req,'app/commonlab/addtesttypes.html',context=context)
    

def retireTestType(req,uuid):
    if req.method == 'POST':
        url = BASE_URL + f'/labtesttype/{uuid}'
        headers = ru.getAuthHeaders(req)
        response = requests.delete(url,headers=headers)
        if response.status_code == 204:
            return redirect('managetesttypes')
    return render(req,'app/commonlab/addtesttypes.html')

def manageAttributes(req,uuid):
    context = {'labTestUuid' : uuid}
    response = ru.getAttributesByLabTest(uuid)
    context['attributes'] = response
    
    
    return render(req,'app/commonlab/manageattributes.html',context=context)


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
        headers = ru.getAuthHeaders(req)
        response = requests.post(url,json=body,headers=headers)
        if response.status_code == 201:
            return redirect(f'/app/commonlab/manageattributes/{uuid}')
        else:
            print(response.status_code)
            print(response.json())
    
        
    return render(req,'app/commonlab/addattributes.html',context=context)


def editAttribute(req,uuid):
    context = {'state' : 'edit' ,}
    url = BASE_URL + f'/labtestattributetype/{uuid}?v=full'
    headers =ru.getAuthHeaders(req)
    response = requests.get(url,headers=headers)
    context['attribute'] = ru.customAttr(response.json(),attributesDataTypes,response.json()['datatypeClassname'],attributesPrefferedHandler,response.json()['preferredHandlerClassname'])
    context['dataTypes'] = ru.removeGivenStrFromObjArr(attributesDataTypes,response.json()['datatypeClassname'],'views')
    context['prefferedHandlers'] = ru.removeGivenStrFromObjArr(attributesPrefferedHandler,response.json()['preferredHandlerClassname'],'views')
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
        headers = ru.getAuthHeaders(req)
        response = requests.post(url,json=body,headers=headers)
        if response.status_code == 200:
            return redirect(f'/commonlab')
        else:
            print(response.status_code)
            print(response.json())
            
    return render(req,'app/commonlab/addattributes.html',context=context)


def managetestorders(req):
    return render(req,'app/commonlab/managetestorders.html')

def managetestsamples(req,uuid):
    return render(req,'app/commonlab/managetestsamples.html')