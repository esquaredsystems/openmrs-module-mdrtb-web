from os import stat
from django.shortcuts import render, redirect
import requests
from django.http import JsonResponse
import base64
import restapi_utils as ru
import commonlab_util as cu
import util


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
    print(req)
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
    status,response = ru.get(req,'commonlab/labtesttype',{'v' : 'full'})
    context = {'response' :response['results'] if status else []}
    return render(req,'app/commonlab/managetesttypes.html',context=context)


def fetch_attributes(req):
    response  = cu.get_attributes_of_labtest(req,req.GET['uuid'])
    attributes  = []
    for attribute in response:
        attributes.append({
            'attrName' : attribute['name'],
            'sortWeight' : attribute['sortWeight'],
            'groupName' : 'none' if attribute['groupName'] == None else attribute['groupName'],
            'multisetName' :'none' if attribute['multisetName'] == None else attribute['multisetName']
        })

    print(attributes)

    return JsonResponse({'attributes' : attributes})



def add_test_type(req):
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
        status,response = cu.add_edit_test_type(req,body,"commonlab/labtesttype")
        if status:
            return redirect('managetesttypes')
        else:
            print(response)
            context['error'] = response
            return render(req,'app/commonlab/addtesttypes.html',context=context)
    concepts = cu.get_commonlab_concepts_by_type(req,'labtesttype')
    context['referenceConcepts'] = concepts
    context['testGroups'] = testGroups
    return render(req,'app/commonlab/addtesttypes.html',context=context)


def edit_test_type(req,uuid):
    context={}
    status,response = ru.get(req,f'commonlab/labtesttype/{uuid}',{'v':'full','lang':'en'})
    if status:
        data = response
        context['state'] = 'edit'
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
        context['referenceConcepts'] = cu.get_commonlab_concepts_by_type(req,'labtesttype')
        context['testGroups'] = util.removeGivenStrFromArr(testGroups,data['testGroup'])
    if req.method == 'POST':
        body = {
        "name" : req.POST['testname'],
        "testGroup" : req.POST['testgroup'],
        "requiresSpecimen": True if req.POST['requirespecimen'] == 'Yes' else False,
        "referenceConcept" : req.POST['referenceconcept'],
        "description" :req.POST['description'],
        "shortName" : None if req.POST['shortname'] == '' else req.POST['shortname'],
        }
        status,response = cu.add_edit_test_type(req,body,f'commonlab/labtesttype/{uuid}')
        if status: 
            return redirect('managetesttypes')


    return render(req,'app/commonlab/addtesttypes.html',context=context)
    

def retire_test_type(req,uuid):
    if req.method == 'POST':
        status,_ = ru.delete(req,f'commonlab/labtesttype/{uuid}')
        if status:
            print(status)
            return redirect('managetesttypes')
    return render(req,'app/commonlab/addtesttypes.html')

def manageAttributes(req,uuid):
    context = {'labTestUuid' : uuid}
    response = cu.get_attributes_of_labtest(req,uuid)
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
        status,response = ru.post(req,'commonlab/labtestattributetype',body)
        if status:
            return redirect(f'/commonlab/labtest/{uuid}/manageattributes')
        else:
            print(response)
    
        
    return render(req,'app/commonlab/addattributes.html',context=context)


def editAttribute(req,uuid):
    context = {'state' : 'edit'}
    status,response = ru.get(req,f'commonlab/labtestattributetype/{uuid}',{'v':"full"})
    if status:
        context['attribute'] = cu.custom_attribute(response,attributesDataTypes,response['datatypeClassname'],attributesPrefferedHandler,response['preferredHandlerClassname'])
        context['dataTypes'] = util.removeGivenStrFromObjArr(attributesDataTypes,response['datatypeClassname'],'views')
        context['prefferedHandlers'] = util.removeGivenStrFromObjArr(attributesPrefferedHandler,response['preferredHandlerClassname'],'views')
    else:
        return redirect(f'/commonlab/manageattributes/{uuid}')
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
        status,response = ru.post(req,f'commonlab/labtestattributetype/{uuid}',body)
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