from django.shortcuts import render, redirect, HttpResponseRedirect, reverse
from django.http import JsonResponse
import utilities.restapi_utils as ru
import utilities.metadata_util as mu
import utilities.commonlab_util as cu
import utilities.patientutls as pu
import utilities.formsutil as fu
import utilities.common_utils as util
import utilities.locationsutil as lu
import json
import datetime
from uuid import uuid4
from django.contrib import messages
from django.core.cache import cache

# start memcache if u havent


def check_if_session_alive(req):
    if 'session_id' not in req.session:
        return False
    return True


def index(req):
    print(req.session['current_location'])
    return render(req, 'app/tbregister/reportmockup.html')


def login(req):
    if 'current_patient' in req.session:
        del req.session['current_patient']
        if 'current_location' in req.session:
            del req.session['current_location']
            if 'current_date_enrolled' in req.session:
                del req.session['current_date_enrolled']
    context = {'title': "Search Patients"}
    session_alive = check_if_session_alive(req)
    if session_alive:
        try:
            minSearchCharacters = mu.get_global_properties(
                req, 'minSearchCharacters')
            context['minSearchCharacters'] = minSearchCharacters
            return render(req, 'app/tbregister/search_patients.html', context=context)
        except Exception as e:
            messages.error(req, 'Error finding global property')
            context['minSearchCharacters'] = 3
            return render(req, 'app/tbregister/search_patients.html', context=context)
    else:
        if req.method == 'POST':
            username = req.POST['username']
            password = req.POST['password']
            response = ru.initiate_session(req, username, password)
            if response:
                if 'redirect' in req.session:
                    return redirect(req.session['redirect'])
                else:
                    return redirect('home')
            else:
                context['title'] = 'Login'
                return render(req, 'app/tbregister/login.html', context=context)
        else:
            context['title'] = 'Login'
            print(context['title'])
            return render(req, 'app/tbregister/login.html', context=context)


def search_patients_query(req):
    if not check_if_session_alive(req):
        redirect('home')

    q = req.GET['q']
    _, response = ru.get(req, 'patient', {'q': q, 'v': 'full'})

    return JsonResponse(response)


def search_patients_view(req):
    # TODO: search for global property 'minSearchCharacters' to specify at least how many keystrokes are required to invoke search
    # no resourse as systemsetting

    return render(req, 'app/tbregister/search_patients.html', context={'title': "Search Patients"})


def enroll_patient(req):
    session_alive = check_if_session_alive(req)
    if session_alive:
        try:
            identifiertypes = mu.get_patient_identifier_types(req)
            locations = json.dumps(lu.create_location_hierarchy(req))
        except Exception as e:
            messages.error(req, e)
            return redirect('home')
        return render(req, 'app/tbregister/enroll_patients.html',
                      context={'locations': locations, 'title': "Enroll new Patient", 'identifiertypes': identifiertypes})
    else:
        return redirect('home')
    if req.method == 'POST':
        patient_info = {
            "identifiers": [
                {
                    "identifier": req.POST['patientidentifier'],
                    "identifierType": req.POST['patientidentifiertype'],
                    "location": req.POST['district'] if 'facility' not in req.POST else req.POST['facility']

                }
            ],
            "person": {
                "names": [{
                    "givenName": req.POST['givenname'],
                    "familyName":req.POST['familyname']
                }],

                "gender": req.POST['gender'],
                "addresses": [{
                    "address1": req.POST['address'],
                    "stateProvince": req.POST['region'],
                    "country": req.POST['country'],
                }]
            }}
        if 'dob' in req.POST:
            patient_info['person']['birthdate'] = req.POST['dob']
            patient_info['person']['birthdateEstimated'] = False
        else:
            patient_info['person']['age'] = req.POST['age']

        if 'deceased' in req.POST:
            patient_info['person']['deathDate'] = req.POST['deathdate']
            patient_info['person']['causeOfDeath'] = req.POST['causeofdeath']
        else:
            patient_info['person']['deathDate'] = None
            patient_info['person']['dead'] = False
            patient_info['person']['causeOfDeath'] = None

        if 'voided' in req.POST:
            patient_info['person']['reasonToVoid'] = req.POST['reasontovoid']

        status, response = ru.post(req, 'patient', patient_info)
        if status:
            return redirect('programenroll', uuid=response['uuid'])
        else:
            messages.error(req, "Error creating patient")
            return redirect('home')


def enroll_in_program(req, uuid):
    session_alive = check_if_session_alive(req)
    if not session_alive:
        return redirect('home')
    context = {'title': 'Add a new Program', 'uuid': uuid}
    if req.method == 'POST':
        body = {
            "patient": uuid,
            "program": req.POST['program'],
            "dateEnrolled": req.POST['enrollmentdate'],
            "location": req.POST.get('district', req.POST.get('facility', None)),
            "dateCompleted": req.POST['completiondate'] if not req.POST['completiondate'] == '' else None,
            "states": [
                {
                    "state": req.POST[work_flow_uuid],
                    "startDate": req.POST['enrollmentdate'],
                    "endDate": req.POST['completiondate'] if not req.POST['completiondate'] == '' else None
                } for work_flow_uuid in pu.get_programs(req, uuid=req.POST['program'], params={'v': 'custom:(allWorkflows)'}) if work_flow_uuid in req.POST
            ]
        }
        try:
            status, response = ru.post(req, 'programenrollment', body)
            if status:
                req.session['current_patient'] = pu.get_patient(
                    req, uuid)
                req.session['current_location'] = {
                    'uuid': response['location']['uuid'],
                    'name': response['location']['name']
                },
                req.session['current+_date_enrolled'] = response['dateEnrolled']
                return redirect(f'/patient/{uuid}/tb03'+'?program={}'.format(req.POST['program']))
        except Exception as e:
            messages.error(req, e)
            return redirect('programenroll', uuid=uuid)

    try:
        programs = pu.get_programs(req)
        locations = json.dumps(lu.create_location_hierarchy(req))
        context['programs'] = programs
        context['jsonprograms'] = json.dumps(programs)
        context['locations'] = locations
    except Exception as e:
        messages.error(req, str(e))
        redirect('programenroll', uuid=uuid)
    return render(req, 'app/tbregister/enroll_program.html', context=context)


def enrolled_programs(req, uuid):
    context = {
        'title': 'Enrolled Programs',
        'uuid': uuid
    }

    programs = pu.get_enrolled_programs_by_patient(req, uuid)
    patient = pu.get_patient(req, uuid)
    if patient:
        context['patient'] = patient
    if programs:
        context['programs'] = programs
    return render(req, 'app/tbregister/enrolled_programs.html', context=context)


def patient_dashboard(req, uuid, mdrtb=None):
    if not check_if_session_alive(req):
        return redirect('home')
    program = req.GET['program']
    context = {'uuid': uuid, 'title': 'Patient Dashboard'}
    if mdrtb:
        patient, program_info = pu.get_patient_dashboard_info(
            req, uuid, program)
        context['mdrtb'] = True
        return render(req, 'app/tbregister/dashboard.html', context=context)
    else:
        patient, program_info, forms = pu.get_patient_dashboard_info(
            req, uuid, program)
        req.session['current_patient'] = patient
        req.session['current_location'] = {
            'uuid': program_info['location']['uuid'],
            'name': program_info['location']['name']
        }
        req.session['current_date_enrolled'] = program_info['dateEnrolled']
        if forms:
            context['forms'] = forms
        if patient and program:
            context['patient'] = patient
            context['program'] = program_info
            return render(req, 'app/tbregister/dashboard.html', context=context)

        else:
            messages.error(req, 'Error fetching patient info')
            return redirect('home')


def tb03_form(req, uuid, formid=None):
    print(req.session['current_location'])
    if not check_if_session_alive(req):
        return redirect('home')

    program = req.GET['program']
    if formid:
        return render(req, 'app/tbregister/dots/tb03.html')

    if req.method == 'POST':
        response = fu.create_tb03(req, uuid, req.POST)
        if not response:
            messages.error(req, 'Error creating TB03')
        return redirect(f'/tbdashboard/patient/{uuid}'+'?program={}'.format(program))
    concept_ids = ["ddf6e09c-f018-4048-a69f-436ff22308b5",
                   "2cd70c1e-955d-428e-86cd-3efc5ecbcabd",
                   "ebde5ed8-4717-472d-9172-599af069e94d",
                   "31b4c61c-0370-102d-b0e3-001ec94a0cc1",
                   "31b94ef8-0370-102d-b0e3-001ec94a0cc1",
                   "3f5a6930-5ead-4880-80ce-6ab79f4f6cb1",
                   "a690e0c4-3371-49b3-9d52-b390fca3dd90",
                   "0f7abf6d-e0bb-46ce-aa69-5214b0d2a295"
                   ]
    concepts = fu.get_form_concepts(concept_ids, req)
    context = {
        "concepts": concepts,
        "title": "TB03",
        'uuid': uuid,
        'patient': req.session['current_patient'],
        'location': req.session['current_location'],
        'enrollment_date': req.session['current_date_enrolled']
    }
    return render(req, 'app/tbregister/dots/tb03.html', context=context)


def transfer(req):
    return render(req, 'app/tbregister/dots/transfer.html', context={'title': "Transfer"})


def tb03u_form(req):
    concept_ids = [
        "31b4c61c-0370-102d-b0e3-001ec94a0cc1",
        "69abc246-13a9-4cbf-92be-83ac59a8938c",
        "4ce4d85b-a5f7-4e0a-ab42-24ebb8778086",
        "37b2cf33-aa3d-4638-95e1-2f886d7eb06c",
        "3f5a6930-5ead-4880-80ce-6ab79f4f6cb1",
        "207a0630-f0af-4208-9a81-326b8c37ebe2",
        "31b94ef8-0370-102d-b0e3-001ec94a0cc1",
        "a690e0c4-3371-49b3-9d52-b390fca3dd90",
        "0f7abf6d-e0bb-46ce-aa69-5214b0d2a295",
    ]

    return render(req, 'app/tbregister/mdr/tb03u.html', context={
        'title': "TB03u",
        "concepts": fu.get_form_concepts(concept_ids, req)
    })


def manage_adverse_events(req):
    context = {'title': 'Manage Adverse Events'}
    return render(req, 'app/tbregister/mdr/manage_ae.html', context=context)


def adverse_events_form(req):
    context = {'title': 'Add Adverse Event'}
    if 'ae_concepts' in req.session:
        context['concepts'] = req.session['ae_concepts']

        return render(req, 'app/tbregister/mdr/adverse_events.html', context=context)
    else:
        concept_ids = ["7047f880-b929-42fc-81f7-b9dbba2d1b15", "1051a25f-5609-40d1-9801-10c3b6fd74ab", "e31fb77b-3623-4c65-ac86-760a2248fc1b", "aa9cb2d0-a6d6-4fb7-bb02-9298235128b2", "aaeb7e1e-e2ea-445d-8c86-6d5eff7d45ad", "d5383d2c-ad69-489e-983d-938bc5356ecf", "34c3a6f2-adf4-4c1a-9e47-7fd9dc4f093d", "	0d5228b4-5891-4740-9b13-1b8898ba4957", "dfad56a0-6f69-437b-bc50-28195039a9e2",
                       "a04a5e94-a584-4f03-b0c5-ea7acf0a28d7", "d9cabe01-9c29-45b0-a071-0cd8d80fcb41", "7e97054b-cf92-49ec-9f68-54b095f5436e", "caa95b8f-86c3-4ec4-9397-933d880aba3e", "1d70fdcd-915d-4524-9ab5-1bdda1790508", "c0592626-62a8-48f6-93b0-1e4f8ff671f3", "adbed9a8-29a6-4adb-8a5b-60619fa02c19", "c213828e-3d30-46a4-9245-485c9f78c233", "dead117a-53c3-40f8-879b-40c170b68037"]
        concepts = fu.get_form_concepts(concept_ids, req)
        req.session['ae_concepts'] = concepts
        context['concepts'] = concepts
        return render(req, 'app/tbregister/mdr/adverse_events.html', context=context)


def drug_resistence_form(req):
    context = {
        'title': "Drug Resistense",
        'concepts': fu.get_form_concepts(["ccd094e6-ac27-418f-a30e-54e9a1bac362"], req)

    }
    return render(req, 'app/tbregister/mdr/drug_resistence.html', context=context)


def manage_regimens(req):
    context = {'title': 'Manage Regimens'}
    return render(req, 'app/tbregister/mdr/manage_regimens.html', context=context)


def regimen_form(req):
    concept_ids = ["483e6ca8-293d-4d00-b71b-4464c093a71d", "3f5a6930-5ead-4880-80ce-6ab79f4f6cb1",
                   "e56514ed-1b3b-4d2e-89f1-564fd6265ebe", "cd9e240f-7860-4e37-a0d2-b922cbcc62d3"]
    context = {
        "title": "Regimen Form",
        "concepts": fu.get_form_concepts(concept_ids, req)
    }
    return render(req, 'app/tbregister/mdr/regimen.html', context=context)


def form_89(req):
    context = {'title': 'Form 89'}
    if 'form89_concepts' in req.session:
        context['concepts'] = req.session['form89_concepts']
        return render(req, 'app/tbregister/dots/form89.html', context=context)
    concept_ids = [
        "1304ac7c-7acb-4df9-864d-fc911fc00028",
        "955fa978-f0a6-4252-bd6d-22b16fba3c1e",
        "e2a0dc12-9af9-4b2d-9b4f-d89463021560",
        "3d16500c-87be-431a-93e6-d517906bd20a",
        "207a0630-f0af-4208-9a81-326b8c37ebe2",
        "06cd622c-ba03-45ec-a65f-96536a14aece",
        "4ce4d85b-a5f7-4e0a-ab42-24ebb8778086",
        "483e6ca8-293d-4d00-b71b-4464c093a71d",
    ]
    concepts = fu.get_form_concepts(concept_ids, req)
    req.session['form89_concepts'] = concepts
    context['concepts'] = concepts
    return render(req, 'app/tbregister/dots/form89.html', context=context)


def patientList(req):
    context = {
        'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December'],
        'quaters': ['1', '2', '3', '4']

    }
    return render(req, 'app/tbregister/patientlist.html', context=context)


def user_profile(req):
    if req.method == 'POST':
        print(req.session['redirect'])
        req.session['locale'] = req.POST['locale']
        return redirect(req.session['redirect'])
    req.session['redirect'] = req.META['HTTP_REFERER']
    return render(req, 'app/tbregister/user_profile.html')


def manage_test_types(req):
    context = {'title': 'Manage Test Types'}
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
    context = {'title': 'Add Test Type'}
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
    context['testGroups'] = cu.get_commonlab_test_groups()
    return render(req, 'app/commonlab/addtesttypes.html', context=context)


def edit_test_type(req, uuid):
    context = {'title': 'Edit Test Type'}
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
        context['testGroups'] = util.remove_given_str_from_arr(
            cu.get_commonlab_test_groups(), data['testGroup'])
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
    context = {'labTestUuid': uuid, 'title': 'Manage Attributes'}
    response = cu.get_attributes_of_labtest(req, uuid)
    context['attributes'] = response

    return render(req, 'app/commonlab/manageattributes.html', context=context)


def addattributes(req, uuid):
    context = {'labTestUuid': uuid, 'prefferedHandlers': cu.get_preffered_handler(),
               'dataTypes': cu.get_attributes_data_types(), 'title': 'Add attributes'}
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


def editAttribute(req, testid, attrid):
    context = {'state': 'edit', 'testid': testid, 'title': 'Edit Attribute'}
    status, response = ru.get(
        req, f'commonlab/labtestattributetype/{attrid}', {'v': "full"})
    if status:
        context['attribute'] = cu.custom_attribute(
            response, response['datatypeClassname'], response['preferredHandlerClassname'])
        context['dataTypes'] = util.remove_given_str_from_obj_arr(
            cu.get_attributes_data_types(), response['datatypeClassname'], 'views')
        context['prefferedHandlers'] = util.remove_given_str_from_obj_arr(
            cu.get_preffered_handler(), response['preferredHandlerClassname'], 'views')
    else:
        redirect(f'/commonlab/labtest/{testid}/manageattributes')
    if req.method == 'POST':
        print(req.POST.get('next', '/'))
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
            req, f'commonlab/labtestattributetype/{attrid}', body)
        if status:

            return redirect(f'/commonlab/labtest/{testid}/manageattributes')
        else:
            print(response.status_code)
            print(response.json())

    return render(req, 'app/commonlab/addattributes.html', context=context)


def managetestorders(req, uuid):
    context = {'title': 'Manage Lab Test Orders', 'patient': uuid}
    status, response = ru.get(req, f'commonlab/labtestorder', {
                              'patient': uuid, 'v': 'custom:(uuid,labTestType,labReferenceNumber,order)'})
    if status:
        context['orders'] = response['results']
        context['json_orders'] = json.dumps(response['results'])
    return render(req, 'app/commonlab/managetestorders.html', context=context)


def add_lab_test(req, uuid):
    context = {'title': 'Add Lab Test', 'patient': uuid}
    if req.method == 'POST':
        body = {
            'labTestType': req.POST['testType'],
            'labReferenceNumber': req.POST['labref'],
            "order": {
                "patient": uuid,
                "concept": cu.get_reference_concept_of_labtesttype(req, req.POST['testType']),
                "encounter": req.POST['encounter'],
                "type": "order",
                "instructions": None if req.POST['instructions'] == None else req.POST['instructions'],
                "orderType": "33ccfcc6-0370-102d-b0e3-001ec94a0cc1",
                "orderer": "09544a0e-14f1-11ed-9181-00155dcead03"

            }
        }
        print(body)
        status, response = ru.post(req, 'commonlab/labtestorder', body)
        if status:
            return redirect('managetestorders', uuid=uuid)
        else:
            print(response)
            messages.error(req, response['error']['message'])
        return redirect('managetestorders', uuid=uuid)
    encounters = cu.get_patient_encounters(req, uuid)
    labtests, testgroups = cu.get_test_groups_and_tests(req)
    if encounters:
        context['encounters'] = encounters['results']
        context['testgroups'] = testgroups
        context['labtests'] = json.dumps(labtests)
    return render(req, 'app/commonlab/addlabtest.html', context=context)


def edit_lab_test(req, patientid, orderid):
    context = {'title': 'Edit Lab Test', 'state': 'edit',
               'orderid': orderid, 'patientid': patientid}
    if req.method == 'POST':
        body = {
            'labTestType': req.POST['testType'],
            'labReferenceNumber': req.POST['labref'],
            "order": {
                "action": "NEW",
                "patient": patientid,
                "concept": cu.get_reference_concept_of_labtesttype(req, req.POST['testType']),
                "encounter": req.POST['encounter'],
                "type": "order",
                "instructions": None if req.POST['instructions'] == None else req.POST['instructions'],
                "orderer": "09544a0e-14f1-11ed-9181-00155dcead03"

            }
        }
        print(body)
        status, response = ru.post(
            req, f'commonlab/labtestorder/{orderid}', body)
        if status:
            return redirect('managetestorders', uuid=patientid)
        else:
            print(response)
            messages.error(req, 'dfsd')
            return redirect('managetestorders', uuid=patientid)
    status, response = ru.get(
        req, f'commonlab/labtestorder/{orderid}', {'v': 'custom:(uuid,order,labTestType,labReferenceNumber)'})
    if status:
        encounters = cu.get_patient_encounters(
            req, response['order']['patient']['uuid'])
        labtests, testgroups = cu.get_test_groups_and_tests(req)
        context['laborder'] = cu.get_custome_lab_order(response)
        context['encounters'] = util.remove_obj_from_objarr(
            encounters['results'], context['laborder']['order']['encounter']['uuid'], 'uuid')
        context['testgroups'] = util.remove_given_str_from_arr(
            testgroups, context['laborder']['labtesttype']['testGroup'])

        context['labtests'] = json.dumps(labtests)
        return render(req, 'app/commonlab/addlabtest.html', context=context)
    else:
        print(response)
        messages.error(req, '404')
        return redirect('managetestorders', uuid=patientid)


def delete_lab_test(req, patientid, orderid):
    status, response = ru.delete(req, f'commonlab/labtestorder/{orderid}')
    if status:
        return redirect('managetestorders', uuid=patientid)
    else:
        print(response)


def managetestsamples(req, orderid):
    context = {'title': 'Manage Test Samples', 'orderid': orderid}
    status, response = ru.get(
        req, f'commonlab/labtestorder/{orderid}', {'v': 'custom:(labTestSamples)'})
    if status:
        context['samples'] = response['labTestSamples']
    return render(req, 'app/commonlab/managetestsamples.html', context=context)


def add_test_sample(req, orderid):
    context = {'title': 'Add Sample', 'orderid': orderid}
    if req.method == 'POST':
        body = {
            "labTest": orderid,
            "specimenType": req.POST['specimentype'],
            "specimenSite":  req.POST['specimensite'],
            "sampleIdentifier":  req.POST['specimenid'],
            "quantity": "" if not req.POST['quantity'] else req.POST['quantity'],
            "units": "" if not req.POST['units'] else req.POST['units'],
            "collectionDate":  req.POST['collectedon'],
            "status": "COLLECTED",
            "collector": "0e5ac8a2-cb48-40ff-a9bd-b0e09afa7860"
        }
        print(body)
        status, response = ru.post(req, 'commonlab/labtestsample', body)
        if status:
            return redirect('managetestsamples', orderid=orderid)
        else:
            print(response)
            messages.error(req, 'Error adding samples')
            return redirect('managetestsamples', orderid=orderid)

    context['specimentype'] = cu.get_commonlab_concepts_by_type(
        req, 'specimentype')
    context['specimensite'] = cu.get_commonlab_concepts_by_type(
        req, 'specimensite')
    context['units'] = cu.get_sample_units(req)

    return render(req, 'app/commonlab/addsample.html', context=context)


def add_test_results(req, orderid):
    context = {'title': 'Add Test Results', 'orderid': orderid}
    if req.method == 'POST':
        status, laborder = ru.get(req, f'commonlab/labtestorder/{orderid}', {})
        if status:
            body = {
                "order": laborder['uuid'],
                "labReferenceNumber": laborder['labReferenceNumber'],
                "labTestType": laborder['labTestType']['uuid'],
                "attributes": []
            }
            for key, value in req.POST.items():
                if value:
                    if value == 'on':
                        body['attributes'].append(
                            {
                                "attributeType": key,
                                "valueReference": True
                            }
                        )
                    elif value == 'off':
                        body['attributes'].append(
                            {
                                "attributeType": key,
                                "valueReference": False
                            }
                        )
                    else:
                        body['attributes'].append(
                            {
                                "attributeType": key,
                                "valueReference": value
                            }
                        )
            body['attributes'].pop(0)
            print(body)
        else:
            messages.error(req, 'Error creating the order')
            return redirect('managetestorders', uuid=req.GET['patient'])
        print(body)
    try:
        attributes, testType = cu.get_custom_attribute_for_labresults(
            req, orderid)
        context['attributes'] = json.dumps(attributes)
        context['testType'] = testType
    except Exception as e:
        messages.error(req, e)
        return redirect('managetestorders', uuid=req.GET['patient'])
    return render(req, 'app/commonlab/addtestresults.html', context=context)


def logout(req):
    status, _ = ru.delete(req, 'session')
    if status:
        ru.clear_session(req)
    return redirect('home')
