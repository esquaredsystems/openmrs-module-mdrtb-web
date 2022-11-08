from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
import utilities.restapi_utils as ru
import utilities.metadata_util as mu
import utilities.commonlab_util as cu
import utilities.common_utils as util


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
        'value': 'org.openmrs.customdatatype.datatype.DateDatatype.name',
        'name': 'Date'
    },
    {
        'value': 'org.openmrs.customdatatype.datatype.BooleanDatatype.name',
        'name': 'Boolean'
    },
    {
        'value': 'org.openmrs.customdatatype.datatype.LongFreeTextDatatype.name',
        'name': 'LongFreeText'
    },
    {
        'value': 'org.openmrs.customdatatype.datatype.FreeTextDatatype.name',
        'name': 'FreeText'
    },
    {
        'value': 'org.openmrs.customdatatype.datatype.RegexValidatedTextDatatype.name',
        'name': 'RegexValidatedText'
    },
    {
        'value': 'org.openmrs.customdatatype.datatype.ConceptDatatype.name',
        'name': 'Concept'
    },








]

attributesPrefferedHandler = [
    {
        'value': 'org.openmrs.web.attribute.handler.DateFieldGenDatatypeHandler',
        'name': 'DateFieldGenDatatype'
    },
    {
        'value': 'org.openmrs.web.attribute.handler.LongFreeTextFileUploadHandler',
        'name': 'LongFreeTextFileUpload'
    },
    {
        'value': 'org.openmrs.web.attribute.handler.BooleanFieldGenDatatypeHandler',
        'name': 'BooleanFieldGenDatatype'
    },
    {
        'value': 'org.openmrs.web.attribute.handler.LongFreeTextTextareaHandler',
        'name': 'LongFreeTextTextarea'
    },








]


def index(req):
    return render(req, 'app/app/tbregister/reportmockup.html')


def login(req):
    if 'session_id' in req.session:
        return render(req, 'app/tbregister/search_patients.html')
    else:
        if req.method == 'POST':
            username = req.POST['username']
            password = req.POST['password']
            response = ru.initiate_session(req, username, password)
            if response:
                return render(req, 'app/tbregister/enroll_without_form.html')
            else:
                context = {'error': response.status_code}
                return render(req, 'app/tbregister/login.html', context=context)
        else:
            return render(req, 'app/tbregister/login.html')


def search_patients_query(req):
    q = req.GET['q']
    _, response = ru.get(req, 'patient', {'q': q, 'v': 'full'})
    return JsonResponse(response)




def search_patients_view(req):
    return render(req, 'app/tbregister/search_patients.html')


def enroll_patient(req):
    if req.method == 'POST':
        person_info = {
            "names": [{
                "givenName": req.POST['givenname'],
                "familyName":req.POST['familyname']
            }],
            "gender": req.POST['gender'],
            "addresses": [{
                "address1": req.POST['address'],
                "cityVillage": req.POST['oblast'],
                "country": req.POST['country'],
            }]
        }
        if 'dob'in req.POST:
            person_info['birthDate'] = req.POST['dob']
        else:
            person_info['age'] = req.POST['age']

        status , response = ru.post(req, 'person', person_info)
        if status:
            print(response['uuid'])
            patient_info = {
                "person" : response['uuid'],
                "identifiers" : [
                    {
                        "identifier" : "00003",
                        "identifierType" : "8d79403a-c2cc-11de-8d13-0010c6dffd0f",
                        "location" : req.POST['district'],
                        "preferred" : False
                    }
                ]
            }
            print(patient_info)
        
            status,patient_res = ru.post(req,'patient',patient_info)
            if status:
                return render(req,'app/tbregister/enroll_program.html')
            else:
                print(patient_res)
                return render(req, 'app/tbregister/enroll_patients.html',context={'error' : patient_res['error']['message']})
        else:
            print(response)
    return render(req, 'app/tbregister/enroll_patients.html')


def enroll_in_dots_program(req):
    return render(req, 'app/tbregister/enroll_program.html')


def tb03_form(req):
    context = {}
    context['messages'] = ''
    return render(req, 'app/tbregister/tb03.html', context=context)


def patientList(req):
    context = {
        'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December'],
        'quaters': ['1', '2', '3', '4']

    }
    return render(req, 'app/tbregister/patientlist.html', context=context)


def patient_dashboard(req, uuid):
    return render(req, 'app/tbregister/dashboard.html')


def user_profile(req):
    if req.method == 'POST':
        req.session['locale'] = req.POST['locale']
        return redirect('home')
    return render(req, 'app/tbregister/user_profile.html')


def logout(req):
    status, response = ru.delete(req, 'session')
    if status:
        ru.clear_session(req)
    return redirect('home')


def concepts(req):
    mu.get_concept(req)
    mu.get_concept_by_uuid('31b4a16e-0370-102d-b0e3-001ec94a0cc1')
    return render(req, 'app/tbregister/dashboard.html')


def manage_test_types(req):
    context = {}
    if req.method == 'POST':
        search_results = cu.get_test_types_by_search(req, req.POST['search'])
        if len(search_results) > 0:
            context['response'] = search_results
            return render(req, 'app/commonlab/managetesttypes.html', context=context)
        else:
            status, response = ru.get(
                req, 'commonlab/labtesttype', {'v': 'full'})
            context['response'] = response['results']
            return render(req, 'app/commonlab/managetesttypes.html', context=context)
    status, response = ru.get(req, 'commonlab/labtesttype', {'v': 'full'})
    context['response'] = response['results'] if status else []
    return render(req, 'app/commonlab/managetesttypes.html', context=context)


def fetch_attributes(req):
    response = cu.get_attributes_of_labtest(req, req.GET['uuid'])
    attributes = []
    for attribute in response:
        attributes.append({
            'attrName': attribute['name'],
            'sortWeight': attribute['sortWeight'],
            'groupName': 'none' if attribute['groupName'] == None else attribute['groupName'],
            'multisetName': 'none' if attribute['multisetName'] == None else attribute['multisetName']
        })

    print(attributes)

    return JsonResponse({'attributes': attributes})


def add_test_type(req):
    context = {}
    if req.method == 'POST':
        body = {
            "name": req.POST['testname'],
            "testGroup": req.POST['testgroup'],
            "requiresSpecimen": True if req.POST['requirespecimen'] == 'Yes' else False,
            "referenceConcept": req.POST['referenceconcept'],
            "description": req.POST['description'],
            "shortName": None if req.POST['shortname'] == '' else req.POST['shortname'],
        }
        status, response = cu.add_edit_test_type(
            req, body, "commonlab/labtesttype")
        if status:
            return redirect('managetesttypes')
        else:
            print(response)
            context['error'] = response
            return render(req, 'app/commonlab/addtesttypes.html', context=context)
    concepts = cu.get_commonlab_concepts_by_type(req, 'labtesttype')
    context['referenceConcepts'] = concepts
    context['testGroups'] = testGroups
    return render(req, 'app/commonlab/addtesttypes.html', context=context)


def edit_test_type(req, uuid):
    context = {}
    status, response = ru.get(
        req, f'commonlab/labtesttype/{uuid}', {'v': 'full', 'lang': 'en'})
    if status:
        data = response
        context['state'] = 'edit'
        context['testType'] = {
            'uuid': data['uuid'],
            'name': data['name'],
            'shortName': data['shortName'],
            'testGroup': data['testGroup'],
            'requiresSpecimen': data['requiresSpecimen'],
            'description': data['description'],
            'referenceConcept': {
                'uuid': data['referenceConcept']['uuid'],
                'name':  data['referenceConcept']['display'],
            }
        }
        context['referenceConcepts'] = cu.get_commonlab_concepts_by_type(
            req, 'labtesttype')
        context['testGroups'] = util.removeGivenStrFromArr(
            testGroups, data['testGroup'])
    if req.method == 'POST':
        body = {
            "name": req.POST['testname'],
            "testGroup": req.POST['testgroup'],
            "requiresSpecimen": True if req.POST['requirespecimen'] == 'Yes' else False,
            "referenceConcept": req.POST['referenceconcept'],
            "description": req.POST['description'],
            "shortName": None if req.POST['shortname'] == '' else req.POST['shortname'],
        }
        status, response = cu.add_edit_test_type(
            req, body, f'commonlab/labtesttype/{uuid}')
        if status:
            return redirect('managetesttypes')

    return render(req, 'app/commonlab/addtesttypes.html', context=context)


def retire_test_type(req, uuid):
    if req.method == 'POST':
        status, _ = ru.delete(req, f'commonlab/labtesttype/{uuid}')
        if status:
            print(status)
            return redirect('managetesttypes')
    return render(req, 'app/commonlab/addtesttypes.html')


def manageAttributes(req, uuid):
    context = {'labTestUuid': uuid}
    response = cu.get_attributes_of_labtest(req, uuid)
    context['attributes'] = response

    return render(req, 'app/commonlab/manageattributes.html', context=context)


def addattributes(req, uuid):
    context = {'labTestUuid': uuid, 'prefferedHandlers': attributesPrefferedHandler,
               'dataTypes': attributesDataTypes}
    if req.method == 'POST':
        body = {
            'labTestType': uuid,
            'name': req.POST['name'],
            'description': req.POST['desc'],
            'datatypeClassname': req.POST['datatype'],
            'sortWeight': float(int(req.POST.get('sortweight', 0.0))),
            'maxOccurs': 0 if req.POST.get('maxoccur') == '' else req.POST.get('maxoccur'),
            'datatypeConfig': req.POST.get('datatypeconfig', ''),
            'preferredHandlerClassname': req.POST.get('handler', ''),
            'groupName': req.POST.get('grpname', ''),
            'multisetName': req.POST.get('mutname', ''),
            'handlerConfig': req.POST.get('handleconfig', ''),

        }
        status, response = ru.post(req, 'commonlab/labtestattributetype', body)
        if status:
            return redirect(f'/commonlab/labtest/{uuid}/manageattributes')
        else:
            print(response)

    return render(req, 'app/commonlab/addattributes.html', context=context)


def editAttribute(req, uuid):
    context = {'state': 'edit'}
    status, response = ru.get(
        req, f'commonlab/labtestattributetype/{uuid}', {'v': "full"})
    if status:
        context['attribute'] = cu.custom_attribute(
            response, attributesDataTypes, response['datatypeClassname'], attributesPrefferedHandler, response['preferredHandlerClassname'])
        context['dataTypes'] = util.removeGivenStrFromObjArr(
            attributesDataTypes, response['datatypeClassname'], 'views')
        context['prefferedHandlers'] = util.removeGivenStrFromObjArr(
            attributesPrefferedHandler, response['preferredHandlerClassname'], 'views')
    else:
        return redirect(f'/commonlab/manageattributes/{uuid}')
    if req.method == 'POST':
        body = {
            'name': req.POST['name'],
            'description': req.POST['desc'],
            'datatypeClassname': req.POST['datatype'],
            'sortWeight': req.POST.get('sortweight', 0.0),
            'maxOccurs': 0 if req.POST.get('maxoccur') == '' else req.POST.get('maxoccur'),
            'datatypeConfig': req.POST.get('datatypeconfig', ''),
            'preferredHandlerClassname': req.POST.get('handler', ''),
            'groupName': req.POST.get('grpname', ''),
            'multisetName': req.POST.get('mutname', ''),
            'handlerConfig': req.POST.get('handleconfig', ''),

        }
        status, response = ru.post(
            req, f'commonlab/labtestattributetype/{uuid}', body)
        if response.status_code == 200:
            return redirect(f'/commonlab')
        else:
            print(response.status_code)
            print(response.json())

    return render(req, 'app/commonlab/addattributes.html', context=context)


def managetestorders(req):
    return render(req, 'app/commonlab/managetestorders.html')


def managetestsamples(req, uuid):
    return render(req, 'app/commonlab/managetestsamples.html')
