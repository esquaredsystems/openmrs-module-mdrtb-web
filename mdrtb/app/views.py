from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
import utilities.restapi_utils as ru
import utilities.metadata_util as mu
import utilities.commonlab_util as cu
import utilities.formsutil as fu
import utilities.common_utils as util
import json
import datetime
from uuid import uuid4
from django.core.cache import cache


def index(req):
    return render(req, 'app/app/tbregister/reportmockup.html')


def login(req):
    context = {'minSearchCharacters': '2', 'title': "Search Patients"}
    if 'session_id' in req.session:
        return render(req, 'app/tbregister/search_patients.html', context=context)
    else:
        if req.method == 'POST':
            username = req.POST['username']
            password = req.POST['password']
            response = ru.initiate_session(req, username, password)
            if response:
                return render(req, 'app/tbregister/search_patients.html')
            else:
                context['error'] = response.status_code
                context['title'] = 'Login'
                return render(req, 'app/tbregister/login.html', context=context)
        else:
            return render(req, 'app/tbregister/login.html')


def search_patients_query(req):
    q = req.GET['q']
    _, response = ru.get(req, 'patient', {'q': q, 'v': 'full'})
    return JsonResponse(response)


def search_patients_view(req):
    # TODO: search for global property 'minSearchCharacters' to specify at least how many keystrokes are required to invoke search
    # no resourse as systemsetting

    return render(req, 'app/tbregister/search_patients.html', context={'title': "Search Patients"})


def enroll_patient(req):
    if req.method == 'POST':
        person_info = {
            "uuid": uuid4(),
            "names": [{
                "givenName": req.POST['givenname'],
                "familyName":req.POST['familyname']
            }],
            "identifiers": [
                {
                    "identifier": "00003",
                    "identifierType": "8d79403a-c2cc-11de-8d13-0010c6dffd0f",
                    "location": req.POST['district'],
                    "preferred": False
                }
            ],
            "gender": req.POST['gender'],
            "addresses": [{
                "address1": req.POST['address'],
                "cityVillage": req.POST['oblast'],
                "country": req.POST['country'],
            }]
        }
        if 'dob' in req.POST:
            person_info['birthDate'] = req.POST['dob']
        else:
            person_info['age'] = req.POST['age']

        if 'deceased' in req.POST:
            person_info['deathDate'] = req.POST['deathdate']
            person_info['causeOfDeath'] = req.POST['causeofdeath']
        elif 'voided' in req.POST:
            person_info['reasonToVoid'] = req.POST['reasontovoid']

        # status , response = ru.post(req, 'person', person_info)
        # if status:
        #     patient_info = {
        #         "person" : response['uuid'],
        #         "identifiers" : [
        #             {
        #                 "identifier" : "00003",
        #                 "identifierType" : "8d79403a-c2cc-11de-8d13-0010c6dffd0f",
        #                 "location" : req.POST['district'],
        #                 "preferred" : False
        #             }
        #         ]
        #     }
        #     status,patient_res = ru.post(req,'patient',patient_info)
        #     if status:
        #         return render(req,'app/tbregister/enroll_program.html')
        #     else:
        #         return render(req, 'app/tbregister/enroll_patients.html',context={'error' : patient_res['error']['message']})
        # else:
        #     print(response)

        # MOCK:
        try:
            cache.set('created_patient', person_info, 5000)
            print('set cache')
            print(cache.get('created_patient'))
            return redirect('dotsEnroll')
        except Exception as e:
            print(e)
            return redirect('home')

    locations = json.dumps(mu.get_locations())
    return render(req, 'app/tbregister/enroll_patients.html', context={'locations': locations, 'title': "Enroll new Patient"})


def enroll_in_dots_program(req):
    locations = json.dumps(mu.get_locations())
    registration_group_concepts = mu.get_concept_by_uuid(
        'ae16bb6e-3d82-4e14-ab07-2018ee10d311', req)['answers']
    registration_group_prev_drug_concepts = mu.get_concept_by_uuid(
        '31c2d590-0370-102d-b0e3-001ec94a0cc1', req)['answers']
    if req.method == 'POST':
        enrollment_info = {
            "enroll_date": req.POST['enrollmentdate'],
            "oblast": req.POST['oblast'],
            "district": req.POST['district'],
            "facility": req.POST['facility'],
            "registration_group_prev_treatment": req.POST['reggrpprevtreatment'],
            "registration_group_prev_drug": req.POST['reggrpprevdrug'],
        }
        try:
            cache.set('enrollment_info', enrollment_info, 5000)
            print('set cache')
        except Exception as e:
            print(e)
        return redirect('tb03')
    return render(req, 'app/tbregister/enroll_program.html', context={'locations': locations, 'reggrp': registration_group_concepts, 'reggrpprev': registration_group_prev_drug_concepts, 'title': "Enroll in Dots Progam"})


def tb03_form(req):
    # TODO: Concepts required IDs = [255,287,261,158,186,435,275,290]
    context = {
        "enrollment_info": cache.get('enrollment_info'),
        "created_patient": cache.get('created_patient'),
        "title": "TB03"
    }
    return render(req, 'app/tbregister/tb03.html', context=context)


def transfer(req):
    return render(req, 'app/tbregister/transfer.html', context={'title': "Transfer"})


def tb03u_form(req):
    # TODO: Concepts required IDs = [453,261,279,]

    return render(req, 'app/tbregister/tb03u.html', context={
        'title': "TB03u"
    })


def adverse_events_form(req):
    # TODO: Concepts required IDs = [244,709,744,745,741,742,743,713,738,739,719,758,759,760,762,726,696,733]
    concepts = fu.get_ae_form_concepts(req)
    return render(req, 'app/tbregister/adverse_events.html', context={'title': 'Adverse Events', 'concepts': concepts})


def drug_resistence_form(req):
    return render(req, 'app/tbregister/drug_resistence.html', context={'title': "Drug Resistense"})


def regimen_form(req):
    # TODO: concept ids = [483e6ca8-293d-4d00-b71b-4464c093a71d,31c2d09a-0370-102d-b0e3-001ec94a0cc1,e56514ed-1b3b-4d2e-89f1-564fd6265ebe,cd9e240f-7860-4e37-a0d2-b922cbcc62d3,]
    return render(req, 'app/tbregister/regimen.html')


def form_89(req):
    return render(req, 'app/tbregister/form89.html', context={'title': 'Form 89'})


def patientList(req):
    context = {
        'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December'],
        'quaters': ['1', '2', '3', '4']

    }
    return render(req, 'app/tbregister/patientlist.html', context=context)


def patient_dashboard(req, uuid):
    status, response = ru.get(req, f'patient/{uuid}', {'v': 'full'})
    if status:
        response['person']['birthdate'] = util.iso_to_normal(
            response['person']['birthdate'])
        return render(req, 'app/tbregister/dashboard.html', context={'patient': response})
    return render(req, 'app/tbregister/dashboard.html', context={
        'error': 'dont have patient'
    })


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
    context['testGroups'] = cu.get_commonlab_test_groups()
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
    context = {'labTestUuid': uuid}
    response = cu.get_attributes_of_labtest(req, uuid)
    context['attributes'] = response

    return render(req, 'app/commonlab/manageattributes.html', context=context)


def addattributes(req, uuid):
    context = {'labTestUuid': uuid, 'prefferedHandlers': cu.get_preffered_handler(),
               'dataTypes': cu.get_attributes_data_types()}
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
            response, response['datatypeClassname'], response['preferredHandlerClassname'])
        context['dataTypes'] = util.removeGivenStrFromObjArr(
            cu.get_attributes_data_types(), response['datatypeClassname'], 'views')
        context['prefferedHandlers'] = util.removeGivenStrFromObjArr(
            cu.get_preffered_handler(), response['preferredHandlerClassname'], 'views')
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
