from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
import utilities.restapi_utils as ru
import utilities.metadata_util as mu
import utilities.commonlab_util as cu
import utilities.patientutls as pu
import utilities.formsutil as fu
import utilities.common_utils as util
import utilities.locationsutil as lu
import json
import traceback
from django.contrib import messages
from django.core.cache import cache
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.privileges import Privileges
from resources.enums.constants import Constants


# start memcache if u havent


def check_if_session_alive(req):
    session_id = req.session.get("session_id")
    if not session_id:
        return False
    return True


def get_redirect_url_from_exception(exception):
    if exception.args[0] == mu.get_global_msgs(
        "auth.session.expired", source="OpenMRS"
    ):
        message, redirect_url = exception.args
        return True, message, redirect_url
    return False, None, None


def index(req):
    context = {}
    try:
        context["url"] = req.session["redirect_url"]
    except Exception as e:
        isexpired, message, redirect = get_redirect_url_from_exception(e)
        if isexpired:
            messages.error(req, message)
            return redirect(redirect)
        messages.error(req, e)
    finally:
        return render(req, "app/tbregister/reportmockup.html", context=context)


def get_locations(req):
    if check_if_session_alive(req):
        try:
            locations = lu.create_location_hierarchy(req)
            if locations:
                return JsonResponse(locations, safe=False)

        except Exception as e:
            print(e)
            messages.error(req, e)
            raise Exception(str(e))
    else:
        return JsonResponse(data={})


def login(req):
    if check_if_session_alive(req):
        redirect_page = req.session.get("redirect_url")
        return redirect(redirect_page if redirect_page else "searchPatientsView")
    context = {"title": "Login"}
    if req.method == "POST":
        username = req.POST["username"]
        password = req.POST["password"]
        try:
            response = ru.initiate_session(req, username, password)
            if response:
                redirect_page = req.session.get("redirect_url")
                return redirect(
                    redirect_page if redirect_page else "searchPatientsView"
                )
            else:
                return render(req, "app/tbregister/login.html", context=context)
        except Exception as e:
            print(e)
            messages.error(req, e)
            return redirect("login")
    else:
        context["title"] = "Login"
        return render(req, "app/tbregister/login.html", context=context)


def search_patients_query(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        q = req.GET["q"]
        _, response = ru.get(req, "patient", parameters={"q": q, "v": "full"})
    except Exception as e:
        messages.error(req, e)
        response = {"error": str(e)}
    return JsonResponse(response)


def search_patients_view(req):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {"title": "Search Patients", "add_patient_privilege": False}
    try:
        if "current_patient_program_flow" in req.session:
            del req.session["current_patient_program_flow"]
        minSearchCharacters = mu.get_global_properties(req, "minSearchCharacters")
        context["minSearchCharacters"] = minSearchCharacters
        # Check if user is admin grant all privileges
        if req.session["logged_user"]["systemId"] == "admin":
            context["add_patient_privilege"] = True
        # Check if user has the privilege to Add patients
        elif mu.check_if_user_has_privilege(
            Privileges.ADD_PATIENTS, req.session["logged_user"]["privileges"]
        ):
            context["add_patient_privilege"] = True
        return render(req, "app/tbregister/search_patients.html", context=context)
    except Exception as e:
        is_expired, message, redirect_url = get_redirect_url_from_exception(e)
        if is_expired:
            messages.error(req, message)
            return redirect(redirect_url)
        context["minSearchCharacters"] = 2
        messages.error(req, str(e))
        return render(req, "app/tbregister/search_patients.html", context=context)


def enroll_patient(req):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            status, response = pu.create_patient(req, req.POST)
            if status:
                return redirect("dotsprogramenroll", uuid=response["uuid"])

        except Exception as e:
            messages.error(req, str(e))
            return redirect("searchPatientsView")
    try:
        req.session["redirect_url"] = req.path
        identifiertypes = mu.get_patient_identifier_types(req)
        return render(
            req,
            "app/tbregister/enroll_patients.html",
            context={"title": "Enroll new Patient", "identifiertypes": identifiertypes},
        )
    except Exception as e:
        messages.error(req, e)
        return redirect("searchPatientsView")


def enrolled_programs(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": "Enrolled Programs",
        "uuid": uuid,
        "dots_program": Constants.DOTS_PROGRAM.value,
    }

    try:
        req.session["redirect_url"] = req.path
        programs = pu.get_enrolled_programs_by_patient(req, uuid)
        patient = pu.get_patient(req, uuid)
        if patient:
            context["patient"] = patient
        if programs:
            context["programs"] = programs
        return render(req, "app/tbregister/enrolled_programs.html", context=context)
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def enroll_in_dots_program(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login", permanent=True)
    context = {"title": "Add a new Program", "uuid": uuid}
    if req.method == "POST":
        try:
            patient_program = pu.enroll_patient_in_program(req, uuid, req.POST)
            if patient_program:
                program = Constants(req.POST["program"]).name.replace("_", " ").title()
                messages.success(
                    req, "Patient Successfully enrolled in {}".format(program)
                )
                req.session["current_patient_program_flow"] = {
                    "current_patient": pu.get_patient(req, uuid),
                    "current_program": pu.get_enrolled_programs_by_patient(
                        req, uuid, enrollment_id=patient_program
                    ),
                }
                return redirect("tb03", uuid=uuid, permanent=True)
            return redirect("dotsprogramenroll", uuid=uuid, permanent=True)
        except Exception as e:
            print(traceback.format_exc())
            messages.error(req, e)
            return redirect("dotsprogramenroll", uuid=uuid, permanent=True)
    else:
        try:
            flow = req.GET.get("flow", None)
            if flow:
                context["flow"] = flow
            program = pu.get_program_by_uuid(req, Constants.DOTS_PROGRAM.value)
            if program:
                context["jsonprogram"] = json.dumps(program)
                return render(
                    req, "app/tbregister/dots/enroll_in_dots.html", context=context
                )
            else:
                messages.error(req, "Error fetching programs. Please try again later")
                return redirect("searchPatientsView")

        except Exception as e:
            messages.error(req, str(e))
            return redirect("/")


def enroll_patient_in_mdrtb(req, uuid):
    context = {"title": "Enroll in MDRTB Program", "uuid": uuid}
    if req.method == "POST":
        try:
            patient_program = pu.enroll_patient_in_program(req, uuid, req.POST)
            if patient_program:
                program = Constants(req.POST["program"]).name.replace("_", " ").title()
                messages.success(
                    req, "Patient Successfully enrolled in {}".format(program)
                )
                req.session["current_patient_program_flow"] = {
                    "current_patient": pu.get_patient(req, uuid),
                    "current_program": pu.get_enrolled_programs_by_patient(
                        req, uuid, enrollment_id=patient_program
                    ),
                }

                return redirect("tb03u", uuid=uuid, permanent=True)

            return redirect("mdrtbprogramenroll", uuid=uuid, permanent=True)
        except Exception as e:
            print(traceback.format_exc())
            messages.error(req, e)
            return redirect("mdrtbprogramenroll", uuid=uuid, permanent=True)
    else:
        try:
            req.session["redirect_url"] = req.path
            program = pu.get_program_by_uuid(req, Constants.MDRTB_PROGRAM.value)
            if program:
                context["jsonprogram"] = json.dumps(program)
                return render(
                    req, "app/tbregister/mdr/enroll_in_mdrtb.html", context=context
                )
            else:
                messages.error(req, "Error fetching programs. Please try again later")
                return redirect("searchPatientsView")

        except Exception as e:
            print(traceback.format_exc())
            messages.error(req, str(e))
            return redirect("mdrtbprogramenroll", uuid=uuid)


def edit_dots_program(req, uuid, programid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        body = {
            "dateEnrolled": req.POST.get("enrollmentdate"),
            "location": req.POST.get("facility") or req.POST.get("district"),
            "dateCompleted": req.POST.get("completiondate"),
        }
        body = {key: value for key, value in body.items() if value}

        try:
            status, response = ru.post(req, f"programenrollment/{programid}", body)
            if status:
                req.session["current_location"] = {
                    "uuid": response["location"]["uuid"],
                    "name": response["location"].get(
                        "name", response["location"]["display"]
                    ),
                }
                req.session["current_date_enrolled"] = response["dateEnrolled"]
                req.session["current_patient_program"] = response["uuid"]
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect("enrolledprograms", uuid=uuid)
    try:
        context = {"title": "Edit Program", "uuid": uuid, "state": "edit"}
        enrolled_program = pu.get_enrolled_program_by_uuid(req, programid)
        context["enrolled_program"] = enrolled_program
        return render(req, "app/tbregister/dots/enroll_in_dots.html", context=context)
    except Exception as e:
        messages.error(req, str(e))
        return redirect("editdotsprogram", uuid=uuid, programid=programid)


def edit_mdrtb_program(req, uuid, programid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        body = {
            "dateEnrolled": req.POST.get("enrollmentdate"),
            "location": req.POST.get("facility") or req.POST.get("district"),
            "dateCompleted": req.POST.get("completiondate"),
        }
        body = {key: value for key, value in body.items() if value}

        try:
            status, response = ru.post(req, f"programenrollment/{programid}", body)
            if status:
                req.session["current_location"] = {
                    "uuid": response["location"]["uuid"],
                    "name": response["location"].get(
                        "name", response["location"]["display"]
                    ),
                }
                req.session["current_date_enrolled"] = response["dateEnrolled"]
                req.session["current_patient_program"] = response["uuid"]
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect("enrolledprograms", uuid=uuid)
    try:
        context = {"title": "Edit Program", "uuid": uuid, "state": "edit"}
        enrolled_program = pu.get_enrolled_program_by_uuid(req, programid)
        context["enrolled_program"] = enrolled_program
        return render(req, "app/tbregister/mdr/enroll_in_mdrtb.html", context=context)
    except Exception as e:
        messages.error(req, str(e))
        return redirect("editmdrtbprogram", uuid=uuid, programid=programid)


def delete_program(req, uuid, programid):
    if programid:
        try:
            status, _ = ru.delete(req, f"programenrollment/{programid}")
            if status:
                messages.warning(req, "Program deleted successfully")
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            messages.error(req, str(e))
            return redirect("enrolledprograms", uuid=uuid)
        finally:
            return redirect("enrolledprograms", uuid=uuid)


def patient_dashboard(req, uuid, mdrtb=None):
    if not check_if_session_alive(req):
        return redirect("login")
    req.session["redirect_url"] = req.path
    req.session["redirect_query_params"] = {
        key: value[0] if len(value) == 1 else value for key, value in req.GET.lists()
    }
    program = req.GET["program"]
    context = {"uuid": uuid, "title": "Patient Dashboard"}
    try:
        req.session["redirect_url"] = req.path

        if mdrtb:
            context["mdrtb"] = True
        patient, program_info, forms = pu.get_patient_dashboard_info(
            req, uuid, program, isMdrtb=True if mdrtb else False
        )

        req.session["current_patient_program_flow"] = {
            "current_patient": patient,
            "current_program": program_info,
        }

        if forms:
            context["forms"] = forms
        if patient and program:
            context["patient"] = patient
            context["program"] = program_info
            return render(req, "app/tbregister/dashboard.html", context=context)

        else:
            messages.error(req, "Error fetching patient info")
            return redirect(req.session["redirect_url"])
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def tb03_form(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_tb03(req, uuid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
        except Exception as e:
            print(traceback.format_exc())
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)
    try:
        req.session["redirect_url"] = req.path

        tb03_concepts = [
            Concepts.TREATMENT_CENTER_FOR_IP.value,
            Concepts.TREATMENT_CENTER_FOR_CP.value,
            Concepts.TUBERCULOSIS_PATIENT_CATEGORY.value,
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.RESULT_OF_HIV_TEST.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.TB_TREATMENT_OUTCOME.value,
            Concepts.CAUSE_OF_DEATH.value,
        ]
        req.session["redirect_url"] = req.path
        concepts = fu.get_form_concepts(tb03_concepts, req)
        context = {
            "concepts": concepts,
            "title": "TB03",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
        }
        return render(req, "app/tbregister/dots/tb03.html", context=context)
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def edit_tb03_form(req, uuid, formid):
    if not check_if_session_alive(req):
        req.session["redirect_url"] = req.path
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_tb03(req, uuid, req.POST, formid=formid)
            if response:
                messages.success(req, "Form updated successfully")
        except Exception as e:
            print(traceback.format_exc())
            messages.error(req, str(e)),
        finally:
            return redirect(req.session["redirect_url"])

    try:
        req.session["redirect_url"] = req.path

        context = {
            "title": "Edit TB03",
            "state": "edit",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
        }
        tb03_concepts = [
            Concepts.TREATMENT_CENTER_FOR_IP.value,
            Concepts.TREATMENT_CENTER_FOR_CP.value,
            Concepts.TUBERCULOSIS_PATIENT_CATEGORY.value,
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.RESULT_OF_HIV_TEST.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.TB_TREATMENT_OUTCOME.value,
            Concepts.CAUSE_OF_DEATH.value,
        ]

        req.session["redirect_url"] = req.path
        form = fu.get_tb03_by_uuid(req, formid)
        concepts = fu.get_form_concepts(tb03_concepts, req)
        fu.remove_tb03_duplicates(concepts, form)
        if form:
            context["form"] = form
            context["concepts"] = concepts
            return render(req, "app/tbregister/dots/tb03.html", context=context)
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def delete_tb03_form(req, formid):
    if formid:
        try:
            response = ru.delete(req, f"mdrtb/tb03/{formid}")
            ru.delete(req, f"encounter/{formid}")
            if response:
                messages.warning(req, "Form deleted")

        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"])


def tb03u_form(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_tb03u(req, uuid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
        except Exception as e:
            print(traceback.format_exc())
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)
    try:
        req.session["redirect_url"] = req.path
        tb03u_concepts = [
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.MDR_STATUS.value,
            Concepts.PRESCRIBED_TREATMENT.value,
            Concepts.TREATMENT_LOCATION.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.METHOD_OF_DETECTION.value,
            Concepts.RESULT_OF_HIV_TEST.value,
            Concepts.MDR_TB_TREATMENT_OUTCOME.value,
            Concepts.CAUSE_OF_DEATH.value,
        ]
        concepts = fu.get_form_concepts(tb03u_concepts, req)
        return render(
            req,
            "app/tbregister/mdr/tb03u.html",
            context={
                "title": "TB03u",
                "concepts": concepts,
                "json": json.dumps(concepts),
                "uuid": uuid,
                "current_patient_program_flow": req.session[
                    "current_patient_program_flow"
                ],
                "identifiers": pu.get_patient_identifiers(req, uuid),
                "constants": {
                    "YES": Concepts.YES.value,
                    "NO": Concepts.NO.value,
                },
            },
        )
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def edit_tb03u_form(req, uuid, formid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_tb03u(req, uuid, req.POST, formid=formid)
        except Exception as e:
            messages.error(req, str(e)),
        finally:
            return redirect(req.session["redirect_url"], permanent=True)

    try:
        req.session["redirect_url"] = req.path
        print(req.session["redirect_url"])
        context = {
            "title": "Edit TB03",
            "state": "edit",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        tb03u_concepts = [
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.MDR_STATUS.value,
            Concepts.PRESCRIBED_TREATMENT.value,
            Concepts.TREATMENT_LOCATION.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.METHOD_OF_DETECTION.value,
            Concepts.RESULT_OF_HIV_TEST.value,
            Concepts.MDR_TB_TREATMENT_OUTCOME.value,
            Concepts.CAUSE_OF_DEATH.value,
        ]

        req.session["redirect_url"] = req.path
        form = fu.get_tb03u_by_uuid(req, formid)
        concepts = fu.get_form_concepts(tb03u_concepts, req)
        fu.remove_tb03u_duplicates(concepts, form)
        if form:
            context["form"] = form
            context["concepts"] = concepts
            return render(req, "app/tbregister/mdr/tb03u.html", context=context)
    except Exception as e:
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def delete_tb03u_form(req, formid):
    if formid:
        try:
            ru.delete(req, f"mdrtb/tb03u/{formid}")
            ru.delete(req, f"encounter/{formid}")
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)


def manage_adverse_events(req, patientid):
    context = {"title": "Manage Adverse Events", "patient_id": patientid}
    return render(req, "app/tbregister/mdr/manage_ae.html", context=context)


def adverse_events_form(req, patientid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_adverse_event(req, patientid, req.POST)
            if response:
                messages.success(req, "From created successfully")
        except Exception as e:
            print(traceback.format_exc())
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)

    try:
        req.session["redirect_url"] = req.path
        context = {
            "title": "Add Adverse Event",
            "patient_id": patientid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        adverse_event_concepts = [
            Concepts.ADVERSE_EVENT.value,
            Concepts.ADVERSE_EVENT_TYPE.value,
            Concepts.SAE_TYPE.value,
            Concepts.SPECIAL_INTEREST_EVENT_TYPE.value,
            Concepts.CAUSALITY_DRUG_1.value,
            Concepts.CAUSALITY_DRUG_2.value,
            Concepts.CAUSALITY_DRUG_3.value,
            Concepts.CAUSALITY_ASSESSMENT_RESULT_1.value,
            Concepts.CAUSALITY_ASSESSMENT_RESULT_2.value,
            Concepts.CAUSALITY_ASSESSMENT_RESULT_3.value,
            Concepts.ACTION_TAKEN_IN_RESPONSE_TO_THE_EVENT.value,
            Concepts.ADVERSE_EVENT_ACTION.value,
            Concepts.ADVERSE_EVENT_ACTION_2.value,
            Concepts.ADVERSE_EVENT_ACTION_3.value,
            Concepts.ADVERSE_EVENT_ACTION_5.value,
            Concepts.ADVERSE_EVENT_OUTCOME.value,
            Concepts.MEDDRA_CODE.value,
            Concepts.DRUG_RECHALLENGE.value,
        ]
        concepts = fu.get_form_concepts(adverse_event_concepts, req)
        context["concepts"] = concepts
        context["jsonconcepts"] = json.dumps(concepts)
        return render(req, "app/tbregister/mdr/adverse_events.html", context=context)
    except Exception as e:
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def edit_adverse_events_form(req, patientid, formid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_adverse_event(
                req, patientid, req.POST, formid=formid
            )
            if response:
                messages.success(req, "Form updated successfully")
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)

    try:
        req.session["redirect_url"] = req.path
        context = {
            "title": "Edit Adverse Event",
            "patient_id": patientid,
            "state": "edit",
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        adverse_event_concepts = [
            Concepts.ADVERSE_EVENT.value,
            Concepts.ADVERSE_EVENT_TYPE.value,
            Concepts.SAE_TYPE.value,
            Concepts.SPECIAL_INTEREST_EVENT_TYPE.value,
            Concepts.CAUSALITY_DRUG_1.value,
            Concepts.CAUSALITY_DRUG_2.value,
            Concepts.CAUSALITY_DRUG_3.value,
            Concepts.CAUSALITY_ASSESSMENT_RESULT_1.value,
            Concepts.CAUSALITY_ASSESSMENT_RESULT_2.value,
            Concepts.CAUSALITY_ASSESSMENT_RESULT_3.value,
            Concepts.ACTION_TAKEN_IN_RESPONSE_TO_THE_EVENT.value,
            Concepts.ADVERSE_EVENT_ACTION.value,
            Concepts.ADVERSE_EVENT_ACTION_2.value,
            Concepts.ADVERSE_EVENT_ACTION_3.value,
            Concepts.ADVERSE_EVENT_ACTION_5.value,
            Concepts.ADVERSE_EVENT_OUTCOME.value,
            Concepts.MEDDRA_CODE.value,
            Concepts.DRUG_RECHALLENGE.value,
        ]
        form = fu.get_ae_by_uuid(req, formid)
        concepts = fu.remove_ae_duplicates(
            fu.get_form_concepts(adverse_event_concepts, req), form
        )

        if form:
            context["form"] = form
            context["concepts"] = concepts
            return render(
                req, "app/tbregister/mdr/adverse_events.html", context=context
            )
    except Exception as e:
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def delete_adverse_events_form(req, formid):
    try:
        status, _ = ru.delete(req, f"mdrtb/adverseevents/{formid}")
        if status:
            messages.success(req, "Form deleted successfully")
    except Exception as e:
        messages.error(req, str(e))
    finally:
        return redirect(req.session["redirect_url"], permanent=True)


def drug_resistence_form(req, patientid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_drug_resistence_form(req, patientid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)

    try:
        req.session["redirect_url"] = req.path
        drug_resistance_concepts = [Concepts.DRUG_RESISTANCE_DURING_TREATMENT.value]
        context = {
            "title": "Drug Resistense",
            "concepts": fu.get_form_concepts(drug_resistance_concepts, req),
            "patient_id": patientid,
        }
        return render(req, "app/tbregister/mdr/drug_resistence.html", context=context)
    except Exception as e:
        is_expired, message, redirect_url = get_redirect_url_from_exception(e)
        if is_expired:
            messages.error(req, message)
            return redirect(redirect_url)
        messages.error(req, str(e))
        return redirect(req.session.get("redirect_url"))


def edit_drug_resistence_form(req, patientid, formid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_drug_resistence_form(
                req, patientid, req.POST, formid=formid
            )
            if response:
                messages.success(req, "Form updated successfully")
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)

    try:
        context = {"title": "Drug Resistanse", "patient_id": patientid, "state": "edit"}
        req.session["redirect_url"] = req.path
        drug_resistance_concepts = [Concepts.DRUG_RESISTANCE_DURING_TREATMENT.value]
        form = fu.get_drug_resistance_form_by_uuid(req, formid)
        concepts = fu.remove_drug_resistance_duplicates(
            fu.get_form_concepts(drug_resistance_concepts, req), form
        )
        if form:
            context["form"] = form
            context["concepts"] = concepts

        return render(req, "app/tbregister/mdr/drug_resistence.html", context=context)
    except Exception as e:
        print(traceback.format_exc())
        is_expired, message, redirect_url = get_redirect_url_from_exception(e)
        if is_expired:
            messages.error(req, message)
            return redirect(redirect_url)
        messages.error(req, str(e))
        return redirect(req.session.get("redirect_url"))


def delete_drug_resistence_form(req, formid):
    try:
        status, _ = ru.delete(req, f"mdrtb/drugresistance/{formid}")
        if status:
            messages.success(req, "Form deleted successfully")
    except Exception as e:
        messages.error(req, e)
    finally:
        return redirect(req.session.get("redirect_url"), permanent=True)


def manage_regimens(req):
    context = {"title": "Manage Regimens"}
    return render(req, "app/tbregister/mdr/manage_regimens.html", context=context)


def regimen_form(req, patientid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_regimen_form(req, patientid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"])

    try:
        req.session["redirect_url"] = req.path
        concept_ids = [
            Concepts.PLACE_OF_CENTRAL_COMMISSION.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.FUNDING_SOURCE.value,
            Concepts.SLD_REGIMEN_TYPE.value,
        ]
        context = {
            "title": "Regimen Form",
            "concepts": fu.get_form_concepts(concept_ids, req),
            "current_patient_program_flow": req.session["current_patient_program_flow"],
        }
        return render(req, "app/tbregister/mdr/regimen.html", context=context)
    except Exception as e:
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def edit_regimen_form(req, patientid, formid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_regimen_form(
                req, patientid, req.POST, formid=formid
            )
            if response:
                messages.success(req, "Form updated successfully")
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"])

    try:
        req.session["redirect_url"] = req.path
        concept_ids = [
            Concepts.PLACE_OF_CENTRAL_COMMISSION.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.FUNDING_SOURCE.value,
            Concepts.SLD_REGIMEN_TYPE.value,
        ]
        form = fu.get_regimen_by_uuid(req, formid)
        context = {
            "title": "Regimen Form",
            "concepts": fu.remove_regimen_duplicates(
                fu.get_form_concepts(concept_ids, req), form
            ),
            "state": "edit",
            "current_patient_program_flow": req.session["current_patient_program_flow"],
        }
        if form:
            context["form"] = form
        else:
            raise Exception("Regimen form not found")

        return render(req, "app/tbregister/mdr/regimen.html", context=context)
    except Exception as e:
        messages.error(req, str(e))
        is_expired, redirect_url = get_redirect_url_from_exception(e)
        if is_expired:
            return redirect(redirect_url)
        return redirect(req.session.get("redirect_url"))


def delete_regimen_form(req, formid):
    try:
        status, _ = ru.delete(req, f"mdrtb/regimen/{formid}")
        if status:
            messages.success(req, "Form deleted successfully")
    except Exception as e:
        messages.error(req, e)
    finally:
        return redirect(req.session.get("redirect_url"))


def form_89(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_form89(req, uuid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
        except Exception as e:
            messages.error(req, str(e))
        finally:
            return redirect(req.session["redirect_url"], permanent=True)

    try:
        req.session["redirect_url"] = req.path
        context = {
            "title": "Form 89",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        form89_concepts = [
            Concepts.LOCATION_TYPE.value,
            Concepts.PROFESSION.value,
            Concepts.POPULATION_CATEGORY.value,
            Concepts.PLACE_OF_DETECTION.value,
            Concepts.CIRCUMSTANCES_OF_DETECTION.value,
            Concepts.METHOD_OF_DETECTION.value,
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.PRESCRIBED_TREATMENT.value,
            Concepts.PLACE_OF_CENTRAL_COMMISSION.value,
        ]
        concepts = fu.get_form_concepts(form89_concepts, req)
        site_of_TB = fu.get_patient_site_of_TB(req, uuid)

        context["concepts"] = concepts
        context["site_of_TB"] = site_of_TB
        return render(req, "app/tbregister/dots/form89.html", context=context)
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def edit_form_89(req, uuid, formid):
    if not check_if_session_alive(req):
        return redirect("login")

    if req.method == "POST":
        try:
            response = fu.create_update_form89(req, uuid, req.POST, formid=formid)
            if response:
                messages.success(req, "Form updated successfully")
        except Exception as e:
            messages.error(req, str(e)),
        finally:
            return redirect(req.session["redirect_url"])

    try:
        req.session["redirect_url"] = req.path

        context = {
            "title": "Edit Form 89",
            "state": "edit",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        form89_concepts = [
            Concepts.LOCATION_TYPE.value,
            Concepts.PROFESSION.value,
            Concepts.POPULATION_CATEGORY.value,
            Concepts.PLACE_OF_DETECTION.value,
            Concepts.CIRCUMSTANCES_OF_DETECTION.value,
            Concepts.METHOD_OF_DETECTION.value,
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.PRESCRIBED_TREATMENT.value,
            Concepts.PLACE_OF_CENTRAL_COMMISSION.value,
        ]
        form = fu.get_form89_by_uuid(req, formid)
        concepts = fu.remove_form89_duplicates(
            fu.get_form_concepts(form89_concepts, req), form
        )
        if form:
            context["form"] = form
            context["concepts"] = concepts
            return render(req, "app/tbregister/dots/form89.html", context=context)
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def delete_form_89(req, formid):
    try:
        ru.delete(req, f"mdrtb/form89/{formid}")
    except Exception as e:
        messages.error(req, str(e))
    finally:
        return redirect(req.session["redirect_url"])


def patientList(req):
    context = {
        "months": [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        "quaters": ["1", "2", "3", "4"],
    }
    return render(req, "app/tbregister/patientlist.html", context=context)


def user_profile(req):
    context = {"title": "User Profile"}
    if req.method == "POST":
        req.session["locale"] = req.POST["locale"]
        return redirect(req.session["redirect_url"])
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        default_locale = req.session.get("logged_user")["userProperties"][
            "defaultLocale"
        ]
        allowed_locales = [
            locale.strip()
            for locale in mu.get_global_properties(req, "locale.allowed.list").split(
                ","
            )
        ]
        allowed_locales.remove(default_locale)
        context["allowed_locales"] = [
            {"name": Constants[locale.upper()].value, "value": locale}
            for locale in allowed_locales
        ]
        context["default_locale"] = {
            "name": Constants[default_locale.upper()].value,
            "value": default_locale,
        }
        return render(req, "app/tbregister/user_profile.html", context=context)
    except Exception as e:
        print(traceback.format_exc())
        messages.error(req, str(e))
        return redirect(req.session["redirect_url"])


def transfer(req):
    return render(
        req, "app/tbregister/dots/transfer.html", context={"title": "Transfer"}
    )


def manage_test_types(req):
    context = {"title": "Manage Test Types"}
    if req.method == "POST":
        search_results = cu.get_test_types_by_search(req, req.POST["search"])
        if len(search_results) > 0:
            context["response"] = search_results
            return render(req, "app/commonlab/managetesttypes.html", context=context)
        else:
            status, response = ru.get(req, "commonlab/labtesttype", {"v": "full"})
            context["response"] = response["results"]
            return render(req, "app/commonlab/managetesttypes.html", context=context)
    status, response = ru.get(req, "commonlab/labtesttype", {"v": "full"})
    context["response"] = response["results"] if status else []
    return render(req, "app/commonlab/managetesttypes.html", context=context)


def fetch_attributes(req):
    response = cu.get_attributes_of_labtest(req, req.GET["uuid"])
    attributes = []
    for attribute in response:
        attributes.append(
            {
                "attrName": attribute["name"],
                "sortWeight": attribute["sortWeight"],
                "groupName": "none"
                if attribute["groupName"] == None
                else attribute["groupName"],
                "multisetName": "none"
                if attribute["multisetName"] == None
                else attribute["multisetName"],
            }
        )
    print(attributes)

    return JsonResponse({"attributes": attributes})


def add_test_type(req):
    context = {"title": "Add Test Type"}
    if req.method == "POST":
        body = {
            "name": req.POST["testname"],
            "testGroup": req.POST["testgroup"],
            "requiresSpecimen": True if req.POST["requirespecimen"] == "Yes" else False,
            "referenceConcept": req.POST["referenceconcept"],
            "description": req.POST["description"],
            "shortName": None if req.POST["shortname"] == "" else req.POST["shortname"],
        }
        status, response = cu.add_edit_test_type(req, body, "commonlab/labtesttype")
        if status:
            return redirect("managetesttypes")
        else:
            print(response)
            context["error"] = response
            return render(req, "app/commonlab/addtesttypes.html", context=context)
    concepts = cu.get_commonlab_concepts_by_type(req, "labtesttype")
    context["referenceConcepts"] = concepts
    context["testGroups"] = cu.get_commonlab_test_groups()
    return render(req, "app/commonlab/addtesttypes.html", context=context)


def edit_test_type(req, uuid):
    context = {"title": "Edit Test Type"}
    status, response = ru.get(
        req, f"commonlab/labtesttype/{uuid}", {"v": "full", "lang": "en"}
    )
    if status:
        data = response
        context["state"] = "edit"
        context["testType"] = {
            "uuid": data["uuid"],
            "name": data["name"],
            "shortName": data["shortName"],
            "testGroup": data["testGroup"],
            "requiresSpecimen": data["requiresSpecimen"],
            "description": data["description"],
            "referenceConcept": {
                "uuid": data["referenceConcept"]["uuid"],
                "name": data["referenceConcept"]["display"],
            },
        }
        context["referenceConcepts"] = cu.get_commonlab_concepts_by_type(
            req, "labtesttype"
        )
        context["testGroups"] = util.remove_given_str_from_arr(
            cu.get_commonlab_test_groups(), data["testGroup"]
        )
    if req.method == "POST":
        body = {
            "name": req.POST["testname"],
            "testGroup": req.POST["testgroup"],
            "requiresSpecimen": True if req.POST["requirespecimen"] == "Yes" else False,
            "referenceConcept": req.POST["referenceconcept"],
            "description": req.POST["description"],
            "shortName": None if req.POST["shortname"] == "" else req.POST["shortname"],
        }
        status, response = cu.add_edit_test_type(
            req, body, f"commonlab/labtesttype/{uuid}"
        )
        if status:
            return redirect("managetesttypes")

    return render(req, "app/commonlab/addtesttypes.html", context=context)


def retire_test_type(req, uuid):
    if req.method == "POST":
        status, _ = ru.delete(req, f"commonlab/labtesttype/{uuid}")
        if status:
            print(status)
            return redirect("managetesttypes")
    return render(req, "app/commonlab/addtesttypes.html")


def manageAttributes(req, uuid):
    context = {"labTestUuid": uuid, "title": "Manage Attributes"}
    response = cu.get_attributes_of_labtest(req, uuid)
    context["attributes"] = response

    return render(req, "app/commonlab/manageattributes.html", context=context)


def addattributes(req, uuid):
    context = {
        "labTestUuid": uuid,
        "prefferedHandlers": cu.get_preffered_handler(),
        "dataTypes": cu.get_attributes_data_types(),
        "title": "Add attributes",
    }
    if req.method == "POST":
        body = {
            "labTestType": uuid,
            "name": req.POST["name"],
            "description": req.POST["desc"],
            "datatypeClassname": req.POST["datatype"],
            "sortWeight": float(int(req.POST.get("sortweight", 0.0))),
            "maxOccurs": 0
            if req.POST.get("maxoccur") == ""
            else req.POST.get("maxoccur"),
            "datatypeConfig": req.POST.get("datatypeconfig", ""),
            "preferredHandlerClassname": req.POST.get("handler", ""),
            "groupName": req.POST.get("grpname", ""),
            "multisetName": req.POST.get("mutname", ""),
            "handlerConfig": req.POST.get("handleconfig", ""),
        }
        status, response = ru.post(req, "commonlab/labtestattributetype", body)
        if status:
            return redirect(f"/commonlab/labtest/{uuid}/manageattributes")
        else:
            print(response)

    return render(req, "app/commonlab/addattributes.html", context=context)


def editAttribute(req, testid, attrid):
    context = {"state": "edit", "testid": testid, "title": "Edit Attribute"}
    status, response = ru.get(
        req, f"commonlab/labtestattributetype/{attrid}", {"v": "full"}
    )
    if status:
        context["attribute"] = cu.custom_attribute(
            response,
            response["datatypeClassname"],
            response["preferredHandlerClassname"],
        )
        context["dataTypes"] = util.remove_given_str_from_obj_arr(
            cu.get_attributes_data_types(), response["datatypeClassname"], "views"
        )
        context["prefferedHandlers"] = util.remove_given_str_from_obj_arr(
            cu.get_preffered_handler(), response["preferredHandlerClassname"], "views"
        )
    else:
        redirect(f"/commonlab/labtest/{testid}/manageattributes")
    if req.method == "POST":
        print(req.POST.get("next", "/"))
        body = {
            "name": req.POST["name"],
            "description": req.POST["desc"],
            "datatypeClassname": req.POST["datatype"],
            "sortWeight": req.POST.get("sortweight", 0.0),
            "maxOccurs": 0
            if req.POST.get("maxoccur") == ""
            else req.POST.get("maxoccur"),
            "datatypeConfig": req.POST.get("datatypeconfig", ""),
            "preferredHandlerClassname": req.POST.get("handler", ""),
            "groupName": req.POST.get("grpname", ""),
            "multisetName": req.POST.get("mutname", ""),
            "handlerConfig": req.POST.get("handleconfig", ""),
        }
        status, response = ru.post(
            req, f"commonlab/labtestattributetype/{attrid}", body
        )
        if status:
            return redirect(f"/commonlab/labtest/{testid}/manageattributes")
        else:
            print(response.status_code)
            print(response.json())

    return render(req, "app/commonlab/addattributes.html", context=context)


def managetestorders(req, uuid):
    context = {"title": "Manage Lab Test Orders", "patient": uuid}
    status, response = ru.get(
        req,
        f"commonlab/labtestorder",
        {"patient": uuid, "v": "custom:(uuid,labTestType,labReferenceNumber,order)"},
    )
    if status:
        context["orders"] = response["results"]
        context["json_orders"] = json.dumps(response["results"])
    return render(req, "app/commonlab/managetestorders.html", context=context)


def add_lab_test(req, uuid):
    context = {"title": "Add Lab Test", "patient": uuid}
    if req.method == "POST":
        body = {
            "labTestType": req.POST["testType"],
            "labReferenceNumber": req.POST["labref"],
            "order": {
                "patient": uuid,
                "concept": cu.get_reference_concept_of_labtesttype(
                    req, req.POST["testType"]
                ),
                "encounter": req.POST["encounter"],
                "type": "order",
                "instructions": None
                if req.POST["instructions"] == None
                else req.POST["instructions"],
                "orderType": "33ccfcc6-0370-102d-b0e3-001ec94a0cc1",
                "orderer": "09544a0e-14f1-11ed-9181-00155dcead03",
            },
        }
        print(body)
        status, response = ru.post(req, "commonlab/labtestorder", body)
        if status:
            return redirect("managetestorders", uuid=uuid)
        else:
            print(response)
            messages.error(req, response["error"]["message"])
        return redirect("managetestorders", uuid=uuid)
    encounters = cu.get_patient_encounters(req, uuid)
    labtests, testgroups = cu.get_test_groups_and_tests(req)
    if encounters:
        context["encounters"] = encounters["results"]
        context["testgroups"] = testgroups
        context["labtests"] = json.dumps(labtests)
    return render(req, "app/commonlab/addlabtest.html", context=context)


def edit_lab_test(req, patientid, orderid):
    context = {
        "title": "Edit Lab Test",
        "state": "edit",
        "orderid": orderid,
        "patientid": patientid,
    }
    if req.method == "POST":
        body = {
            "labTestType": req.POST["testType"],
            "labReferenceNumber": req.POST["labref"],
            "order": {
                "action": "NEW",
                "patient": patientid,
                "concept": cu.get_reference_concept_of_labtesttype(
                    req, req.POST["testType"]
                ),
                "encounter": req.POST["encounter"],
                "type": "order",
                "instructions": None
                if req.POST["instructions"] == None
                else req.POST["instructions"],
                "orderer": "09544a0e-14f1-11ed-9181-00155dcead03",
            },
        }
        print(body)
        status, response = ru.post(req, f"commonlab/labtestorder/{orderid}", body)
        if status:
            return redirect("managetestorders", uuid=patientid)
        else:
            print(response)
            messages.error(req, "dfsd")
            return redirect("managetestorders", uuid=patientid)
    status, response = ru.get(
        req,
        f"commonlab/labtestorder/{orderid}",
        {"v": "custom:(uuid,order,labTestType,labReferenceNumber)"},
    )
    if status:
        encounters = cu.get_patient_encounters(
            req, response["order"]["patient"]["uuid"]
        )
        labtests, testgroups = cu.get_test_groups_and_tests(req)
        context["laborder"] = cu.get_custome_lab_order(response)
        context["encounters"] = util.remove_obj_from_objarr(
            encounters["results"],
            context["laborder"]["order"]["encounter"]["uuid"],
            "uuid",
        )
        context["testgroups"] = util.remove_given_str_from_arr(
            testgroups, context["laborder"]["labtesttype"]["testGroup"]
        )

        context["labtests"] = json.dumps(labtests)
        return render(req, "app/commonlab/addlabtest.html", context=context)
    else:
        print(response)
        messages.error(req, "404")
        return redirect("managetestorders", uuid=patientid)


def delete_lab_test(req, patientid, orderid):
    status, response = ru.delete(req, f"commonlab/labtestorder/{orderid}")
    if status:
        return redirect("managetestorders", uuid=patientid)
    else:
        print(response)


def managetestsamples(req, orderid):
    context = {"title": "Manage Test Samples", "orderid": orderid}
    status, response = ru.get(
        req, f"commonlab/labtestorder/{orderid}", {"v": "custom:(labTestSamples)"}
    )
    if status:
        context["samples"] = response["labTestSamples"]
    return render(req, "app/commonlab/managetestsamples.html", context=context)


def add_test_sample(req, orderid):
    context = {"title": "Add Sample", "orderid": orderid}
    if req.method == "POST":
        body = {
            "labTest": orderid,
            "specimenType": req.POST["specimentype"],
            "specimenSite": req.POST["specimensite"],
            "sampleIdentifier": req.POST["specimenid"],
            "quantity": "" if not req.POST["quantity"] else req.POST["quantity"],
            "units": "" if not req.POST["units"] else req.POST["units"],
            "collectionDate": req.POST["collectedon"],
            "status": "COLLECTED",
            "collector": "0e5ac8a2-cb48-40ff-a9bd-b0e09afa7860",
        }
        print(body)
        status, response = ru.post(req, "commonlab/labtestsample", body)
        if status:
            return redirect("managetestsamples", orderid=orderid)
        else:
            print(response)
            messages.error(req, "Error adding samples")
            return redirect("managetestsamples", orderid=orderid)

    context["specimentype"] = cu.get_commonlab_concepts_by_type(req, "specimentype")
    context["specimensite"] = cu.get_commonlab_concepts_by_type(req, "specimensite")
    context["units"] = cu.get_sample_units(req)

    return render(req, "app/commonlab/addsample.html", context=context)


def add_test_results(req, orderid):
    context = {"title": "Add Test Results", "orderid": orderid}
    if req.method == "POST":
        status, laborder = ru.get(req, f"commonlab/labtestorder/{orderid}", {})
        if status:
            body = {
                "order": laborder["uuid"],
                "labReferenceNumber": laborder["labReferenceNumber"],
                "labTestType": laborder["labTestType"]["uuid"],
                "attributes": [],
            }
            for key, value in req.POST.items():
                if value:
                    if value == "on":
                        body["attributes"].append(
                            {"attributeType": key, "valueReference": True}
                        )
                    elif value == "off":
                        body["attributes"].append(
                            {"attributeType": key, "valueReference": False}
                        )
                    else:
                        body["attributes"].append(
                            {"attributeType": key, "valueReference": value}
                        )
            body["attributes"].pop(0)
            print(body)
        else:
            messages.error(req, "Error creating the order")
            return redirect("managetestorders", uuid=req.GET["patient"])
        print(body)
    try:
        attributes, testType = cu.get_custom_attribute_for_labresults(req, orderid)
        context["attributes"] = json.dumps(attributes)
        context["testType"] = testType
    except Exception as e:
        messages.error(req, e)
        return redirect("managetestorders", uuid=req.GET["patient"])
    return render(req, "app/commonlab/addtestresults.html", context=context)


def logout(req):
    try:
        status, _ = ru.delete(req, "session")
        if status:
            ru.clear_session(req)
            return redirect("login")
    except Exception as e:
        messages.error(req, str(e))
        return redirect(req.session.get("redirect_url"))
