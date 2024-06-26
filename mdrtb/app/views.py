from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime
import utilities.restapi_utils as ru
import utilities.metadata_util as mu
from django.core.cache import cache
import utilities.commonlab_util as cu
import utilities.patient_utils as pu
import utilities.forms_util as fu
import utilities.common_utils as util
import utilities.locations_util as lu
import json
import datetime
import logging
from django.contrib import messages
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.privileges import Privileges
from resources.enums.constants import Constants
from resources.enums.encounterType import EncounterType
from mdrtb.settings import REST_API_BASE_URL

logger = logging.getLogger("django")


def check_if_session_alive(req):
    session_id = req.session.get("session_id")
    if not session_id:
        return False
    return True


def check_privileges(req, privileges_required):
    perms = {}
    for privilege in privileges_required:
        perms[privilege.name.lower() + "_privilege"] = mu.check_if_user_has_privilege(
            req, privilege.value, req.session["logged_user"]["user"]["privileges"]
        )
    return perms


def index(req):
    # This is a test function
    context = {"title": "TB03 parameteres"}
    return render(req, "app/tbregister/reportmockup.html", context=context)


def get_locations(req):
    """
    This function will fetch the locations in a levels hierarchy
    """
    if check_if_session_alive(req):
        try:
            locations = lu.create_location_hierarchy(req)
            if locations:
                logger.info("Locations fetched successfully")
                return JsonResponse(locations, safe=False)
        except Exception as e:
            log_and_show_error(e, req)
            raise Exception(str(e))
    else:
        return JsonResponse(data={})


def change_locale(req, locale):
    locale = locale
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    try:
        req.session["locale"] = locale
        cache.clear()
        mu.get_all_concepts(req)
        lu.create_location_hierarchy(req)
        logged_in_user_uuid = req.session["logged_user"]["user"]["uuid"]
        user_properties = req.session["logged_user"]["user"]["userProperties"]
        user_properties["defaultLocale"] = locale
        _, _ = ru.post(
            req,
            f"user/{logged_in_user_uuid}",
            {"userProperties": user_properties},
        )
        return redirect(req.session["redirect_url"])
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def get_concepts(req, uuid=None):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        url = f"concept/{uuid}" if uuid else "concept"
        params = {}
        if "q" in req.GET:
            params["q"] = req.GET["q"]
        _, response = ru.get(req, url, parameters=params)
    except Exception as e:
        log_and_show_error(e, req)
        response = {"error": str(e)}
    return JsonResponse(response)


def render_login(req):
    if check_if_session_alive(req):
        redirect_page = req.session.get("redirect_url")
        logger.info("Redirecting from login page")
        return redirect(redirect_page if redirect_page else "searchPatientsView")
    context = {"title": mu.get_global_msgs("auth.login", locale="ru", source="OpenMRS")}
    if req.method == "POST":
        username = req.POST.get("username")
        password = req.POST.get("password")
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
            log_and_show_error(e, req)
            return redirect("login")
    else:
        context["title"] = mu.get_global_msgs(
            "auth.login", locale="ru", source="OpenMRS"
        )
        return render(req, "app/tbregister/login.html", context=context)


def search_patients_query(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        q = req.GET["q"]
        _, response = ru.get(req, "patient", parameters={"q": q, "v": "full"})
    except Exception as e:
        log_and_show_error(e, req)
        response = {"error": str(e)}
    return JsonResponse(response)


def render_search_patients_view(req):
    if not check_if_session_alive(req):
        return redirect("login")
    title = (
        mu.get_global_msgs(
            "general.search", locale=req.session["locale"], source="OpenMRS"
        )
        + " "
        + mu.get_global_msgs("general.patient", locale=req.session["locale"], source="OpenMRS")
    )
    context = {"title": title}
    privileges_required = [
        Privileges.GET_PATIENTS,
        Privileges.ADD_PATIENTS,
    ]
    try:
        if "breadcrumbs" in req.session:
            del req.session["breadcrumbs"]
        if "current_patient_program_flow" in req.session:
            del req.session["current_patient_program_flow"]
        min_search_characters = mu.get_global_properties(req, "minSearchCharacters")
        context["minSearchCharacters"] = min_search_characters
        context.update(check_privileges(req, privileges_required))
        return render(req, "app/tbregister/search_patients.html", context=context)
    except Exception as e:
        context["minSearchCharacters"] = 2
        log_and_show_error(e, req)
        return render(req, "app/tbregister/search_patients.html", context=context)


def render_enroll_patient(req):
    if not check_if_session_alive(req):
        return redirect("login")
    title = mu.get_global_msgs("mdrtb.enrollNewPatient", locale=req.session["locale"])
    context = {"title": title}
    if req.method == "POST":
        try:
            # Some UUIDs should be sent as actual text values
            status, response = pu.save_patient(req, req.POST)
            if status:
                return redirect("dotsprogramenroll", uuid=response["uuid"])
        except Exception as e:
            log_and_show_error(e, req)
    try:
        privileges_required = [Privileges.ADD_PATIENTS]
        context.update(check_privileges(req, privileges_required))
        if not context["add_patients_privilege"]:
            raise Exception("Privileges required: Add Patients")
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        context["identifiertypes"] = mu.get_patient_identifier_types(req)
        mu.add_url_to_breadcrumb(req, context["title"])
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return render(
            req,
            "app/tbregister/enroll_patients.html",
            context=context,
        )


def render_edit_patient(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    title = mu.get_global_msgs("mdrtb.enrollNewPatient", locale=req.session["locale"])
    context = {"title": title}
    if req.method == "POST":
        try:
            status, response = pu.save_patient(req, req.POST, uuid)
            if status:
                return redirect("enrolledprograms", uuid=uuid)
        except Exception as e:
            log_and_show_error(e, req)
    else:
        privileges_required = [Privileges.ADD_PATIENTS]
        context.update(check_privileges(req, privileges_required))
        if not context["add_patients_privilege"]:
            raise Exception("Privileges required: Add Patients")
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        context["identifiertypes"] = mu.get_patient_identifier_types(req)
        mu.add_url_to_breadcrumb(req, context["title"])
        context["patient"] = pu.get_patient(req, uuid)
        if context["patient"]["identifiers"]:
            context["patient"]["dotsidentifier"] = context["patient"]["identifiers"][0]["identifier"]

        return render(req, "app/tbregister/edit_patient.html", context=context)


def render_enrolled_programs(req, uuid):
    privileges_required = [Privileges.VIEW_PATIENT_PROGRAMS]
    if not check_if_session_alive(req):
        return redirect("login")
    title = (
        mu.get_global_msgs(
            "Program.enrolled", locale=req.session["locale"], source="OpenMRS"
        )
        + " "
        + mu.get_global_msgs(
            "Program.header", locale=req.session["locale"], source="OpenMRS"
        )
    )
    context = {
        "title": title,
        "uuid": uuid,
        "dots_program": Constants.DOTS_PROGRAM.value,
    }
    try:
        context.update(check_privileges(req, privileges_required))
        if not context["view_patient_programs_privilege"]:
            raise Exception("Privileges required: View patient programs")
        mu.add_url_to_breadcrumb(req, context["title"])
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        programs = pu.get_enrolled_programs_by_patient(req, uuid)
        patient = pu.get_patient(req, uuid)
        if patient:
            context["patient"] = patient
        if programs:
            context["programs"] = programs
            lab_results = cu.get_lab_test_orders_for_dashboard(req, uuid)
            if lab_results:
                context["lab_results"] = lab_results
                context["lab_json"] = json.dumps(lab_results)
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return render(req, "app/tbregister/enrolled_programs.html", context=context)


def render_enroll_in_dots_program(req, uuid):
    privileges_required = [Privileges.ADD_PATIENT_PROGRAMS]
    if not check_if_session_alive(req):
        return redirect("login", permanent=True)
    title = mu.get_global_msgs(
        "Program.add", locale=req.session["locale"], source="OpenMRS"
    )
    context = {"title": title, "uuid": uuid}
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
                return redirect("tb03", uuid=uuid)
            else:
                raise Exception("Couldn't enroll patient in progarm")
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("dotsprogramenroll", uuid=uuid)
    try:
        enrolled_location = req.session.get("location_enrolled_in", None)
        context["enrolled_location"] = enrolled_location
        context.update(check_privileges(req, privileges_required))
        if not context["add_patient_programs_privilege"]:
            raise Exception("Privileges required: Add patient programs")
        program = pu.get_program_by_uuid(req, Constants.DOTS_PROGRAM.value)
        if program:
            context["jsonprogram"] = json.dumps(program)
            mu.add_url_to_breadcrumb(req, context["title"])
            # Check for a DOTS identifier to auto-fill
            patient_identifiers = pu.get_patient_identifiers(req, uuid)
            if patient_identifiers.get("dots"):
                context["dotsidentifier"] = patient_identifiers["dots"]
            return render(
                req, "app/tbregister/dots/enroll_in_dots.html", context=context
            )
        else:
            log_and_show_error("Error fetching programs. Please try again later", req)
            return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return render(req, "app/tbregister/dots/enroll_in_dots.html", context=context)


def render_enroll_patient_in_mdrtb(req, uuid):
    privileges_required = [Privileges.ADD_PATIENT_PROGRAMS]
    title = mu.get_global_msgs(
        "mdrtb.enrollment.enrollMdrtb", locale=req.session["locale"]
    )
    context = {"title": title, "uuid": uuid}
    if req.method == "POST":
        try:
            patient_program = pu.enroll_patient_in_program(req, uuid, req.POST)
            if not patient_program:
                raise Exception("Error enrolling patient in MDRTB program")
            program = Constants(req.POST["program"]).name.replace("_", " ").title()
            messages.success(req, "Patient Successfully enrolled in {}".format(program))
            req.session["current_patient_program_flow"] = {
                "current_patient": pu.get_patient(req, uuid),
                "current_program": pu.get_enrolled_programs_by_patient(
                    req, uuid, enrollment_id=patient_program
                ),
            }
            return redirect("tb03u", uuid=uuid)
        except Exception as e:
            log_and_show_error(e, req)
            return render(
                req, "app/tbregister/mdr/enroll_in_mdrtb.html", context=context
            )
    try:
        context.update(check_privileges(req, privileges_required))
        if not context["add_patient_programs_privilege"]:
            raise Exception("Privileges required: Add patient programs")
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        program = pu.get_program_by_uuid(req, Constants.MDRTB_PROGRAM.value)
        tb03s = fu.get_patient_tb03_forms(req, uuid)
        # Fetch the last TB03 form filled
        if tb03s:
            context["tb03"] = tb03s[-1]
        if program:
            context["jsonprogram"] = json.dumps(program)
        else:
            log_and_show_error("Error fetching programs. Please try again later", req)
            return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return render(req, "app/tbregister/mdr/enroll_in_mdrtb.html", context=context)


def render_edit_dots_program(req, uuid, programid):
    privileges_required = [
        Privileges.EDIT_PATIENT_PROGRAMS,
        Privileges.EDIT_DOTS_MDR_DATA,
    ]
    title = mu.get_global_msgs("mdrtb.editProgram", locale=req.session["locale"])
    context = {"title": title, "uuid": uuid, "state": "edit"}
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
                return redirect("enrolledprograms", uuid=uuid)
        except Exception as e:
            log_and_show_error(e, req)
            return render(
                req, "app/tbregister/dots/enroll_in_dots.html", context=context
            )
    try:
        context.update(check_privileges(req, privileges_required))
        if not context["edit_patient_programs_privilege"]:
            raise Exception("Privileges required: Edit patient programs")
        enrolled_program = pu.get_enrolled_program_by_uuid(req, programid)
        context["enrolled_program"] = enrolled_program
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/dots/enroll_in_dots.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("editdotsprogram", uuid=uuid, programid=programid)


def render_edit_mdrtb_program(req, uuid, programid):
    privileges_required = [
        Privileges.EDIT_PATIENT_PROGRAMS,
        Privileges.EDIT_DOTS_MDR_DATA,
    ]
    if not check_if_session_alive(req):
        return redirect("login")
    title = mu.get_global_msgs("mdrtb.editProgram", locale=req.session["locale"])
    context = {"title": title, "uuid": uuid, "state": "edit"}
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
                return redirect("enrolledprograms", uuid=uuid)
        except Exception as e:
            log_and_show_error(e, req)
            return render(
                req, "app/tbregister/mdr/enroll_in_mdrtb.html", context=context
            )
    try:
        context.update(check_privileges(req, privileges_required))
        if not context["edit_patient_programs_privilege"]:
            raise Exception("Privileges required: Edit patient programs")
        enrolled_program = pu.get_enrolled_program_by_uuid(req, programid)
        context["enrolled_program"] = enrolled_program
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/mdr/enroll_in_mdrtb.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("editmdrtbprogram", uuid=uuid, programid=programid)


def render_patient_dashboard(req, uuid, mdrtb=None):
    privileges_required = [
        Privileges.PATIENT_DASHBOARD_VIEW_FORMS_SECTION,
        Privileges.PATIENT_DASHBOARD_VIEW_OVERVIEW_SECTION,
        Privileges.VIEW_ENCOUNTERS,
        Privileges.ADD_ENCOUNTERS,
        Privileges.EDIT_ENCOUNTERS,
        Privileges.EDIT_ENCOUNTERS,
        Privileges.ADD_PATIENT_PROGRAMS,
        Privileges.VIEW_COMMONLABTEST_RESULTS,
    ]
    if not check_if_session_alive(req):
        return redirect("login")
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    query_params = {
        key: value[0] if len(value) == 1 else value for key, value in req.GET.lists()
    }
    req.session["redirect_query_params"] = query_params
    program = req.GET["program"]
    title = mu.get_global_msgs("mdrtb.patientDashboard", locale=req.session["locale"])
    context = {"uuid": uuid, "title": title}
    try:
        context.update(check_privileges(req, privileges_required))
        if not context["view_encounters_privilege"]:
            raise Exception("Privileges required: View Encounters")
        mu.add_url_to_breadcrumb(req, context["title"], query_params=query_params)
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        if mdrtb:
            context["mdrtb"] = True
        (
            patient,
            program_info,
            treatment_outcome,
            transfer_out,
            forms,
            lab_results,
        ) = pu.get_patient_dashboard_info(
            req, uuid, program, is_mdrtb=mdrtb is not None, get_lab_data=True
        )
        # Remove Hospitalization Workflow
        if program_info.get("states"):
            program_info["states"] = [item for item in program_info["states"] if item['concept'] != 'Hospitalization Workflow']
        req.session["current_patient_program_flow"] = {
            "current_patient": patient,
            "current_program": program_info,
        }
        if lab_results:
            context["lab_results"] = lab_results
            context["lab_json"] = json.dumps(lab_results)
        if forms:
            context["forms"] = forms
        if transfer_out:
            context["transfer_out"] = transfer_out[0]
        if patient and program:
            context["patient"] = patient
            context["program"] = program_info
            context["treatment_outcome"] = treatment_outcome
            context["mdrEnrolled"] = pu.check_if_patient_enrolled_in_mdrtb(req, uuid)
        else:
            log_and_show_error("Error fetching patient info", req)
            return redirect(req.session["redirect_url"])
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return render(req, "app/tbregister/dashboard.html", context=context)


def render_tb03_form(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_tb03(req, uuid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
                redirect_to = "/tbdashboard/patient/{}?program={}".format(
                    uuid,
                    req.session["current_patient_program_flow"]["current_program"][
                        "uuid"
                    ],
                )
                return redirect(redirect_to)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("tb03", uuid=uuid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
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
        title = mu.get_global_msgs("mdrtb.tb03", locale=req.session["locale"])
        concepts = fu.get_form_concepts(tb03_concepts, req)
        context = {
            "concepts": concepts,
            "title": title,
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
        }
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/dots/tb03.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("tb03", uuid=uuid)


def render_edit_tb03_form(req, uuid, formid):
    privileges_required = [Privileges.DELETE_ENCOUNTERS]
    if not check_if_session_alive(req):
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_tb03(req, uuid, req.POST, formid=formid)
            if response:
                messages.success(req, "Form updated successfully")
                return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("edittb03", uuid=uuid, formid=formid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = (
                mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                + " "
                + mu.get_global_msgs("mdrtb.tb03", locale=req.session["locale"])
        )
        context = {
            "title": title,
            "state": "edit",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
        }
        context.update(check_privileges(req, privileges_required))
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
        mu.add_url_to_breadcrumb(req, context["title"])
        form = fu.get_tb03_by_uuid(req, formid)
        concepts = fu.get_form_concepts(tb03_concepts, req)
        fu.remove_tb03_duplicates(concepts, form)
        if form:
            context["form"] = form
            context["concepts"] = concepts
            return render(req, "app/tbregister/dots/tb03.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("edittb03", uuid=uuid, formid=formid)


def render_delete_tb03_form(req, formid):
    if formid:
        try:
            response = ru.delete(req, f"mdrtb/tb03/{formid}")
            ru.delete(req, f"encounter/{formid}")
            if response:
                messages.warning(req, "Form deleted")
        except Exception as e:
            log_and_show_error(e, req)
        finally:
            return redirect(req.session["redirect_url"])


def render_tb03u_form(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_tb03u(req, uuid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
                redirect_to = "/mdrtb/dashboard/patient/{}?program={}".format(
                    uuid,
                    req.session["current_patient_program_flow"]["current_program"]["uuid"],
                )
                return redirect(redirect_to)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("tb03u", uuid=uuid)

    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
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
        title = mu.get_global_msgs("mdrtb.tb03u", locale=req.session["locale"])
        context = {
            "title": title,
            "concepts": concepts,
            "json": json.dumps(concepts),
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/mdr/tb03u.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("tb03u", uuid=uuid)


def render_edit_tb03u_form(req, uuid, formid):
    privileges_required = [Privileges.DELETE_ENCOUNTERS]
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            fu.create_update_tb03u(req, uuid, req.POST, formid=formid)
            return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("edittb03u", uuid=uuid, formid=formid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = (
                mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                + " "
                + mu.get_global_msgs("mdrtb.tb03u", locale=req.session["locale"])
        )
        context = {
            "title": title,
            "state": "edit",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        context.update(check_privileges(req, privileges_required))
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
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        form = fu.get_tb03u_by_uuid(req, formid)
        concepts = fu.get_form_concepts(tb03u_concepts, req)
        fu.remove_tb03u_duplicates(concepts, form)
        if form:
            context["form"] = form
            context["concepts"] = concepts
            mu.add_url_to_breadcrumb(req, context["title"])
            return render(req, "app/tbregister/mdr/tb03u.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("edittb03u", uuid=uuid, formid=formid)


def render_delete_tb03u_form(req, formid):
    if formid:
        try:
            ru.delete(req, f"mdrtb/tb03u/{formid}")
            ru.delete(req, f"encounter/{formid}")
        except Exception as e:
            log_and_show_error(e, req)
        finally:
            return redirect(req.session["redirect_url"], permanent=True)


def render_adverse_events_form(req, patientid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_adverse_event(req, patientid, req.POST)
            if response:
                messages.success(req, "From created successfully")
                return redirect(req.session["redirect_url"], permanent=True)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("adverseevents", patientid=patientid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = mu.get_global_msgs("mdrtb.pv.aeForm", locale=req.session["locale"])
        context = {
            "title": title,
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
            Concepts.ADVERSE_EVENT_ACTION.value,
            Concepts.ADVERSE_EVENT_ACTION_2.value,
            Concepts.ADVERSE_EVENT_ACTION_3.value,
            Concepts.ADVERSE_EVENT_ACTION_4.value,
            Concepts.ADVERSE_EVENT_ACTION_5.value,
            Concepts.ADVERSE_EVENT_OUTCOME.value,
            Concepts.DRUG_RECHALLENGE.value,
        ]
        concepts = fu.get_form_concepts(adverse_event_concepts, req)
        context["concepts"] = concepts
        context["jsonconcepts"] = json.dumps(concepts)
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/mdr/adverse_events.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("adverseevents", patientid=patientid)


def render_edit_adverse_events_form(req, patientid, formid):
    privileges_required = [Privileges.DELETE_ENCOUNTERS]
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_adverse_event(
                req, patientid, req.POST, formid=formid
            )
            if response:
                messages.success(req, "Form updated successfully")
                return redirect(req.session["redirect_url"], permanent=True)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("editadverseevents", uuid=patientid, formid=formid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = (
                mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                + " "
                + mu.get_global_msgs("mdrtb.pv.aeForm", locale=req.session["locale"])
        )
        context = {
            "title": title,
            "patient_id": patientid,
            "state": "edit",
            "current_patient_program_flow": req.session.get(
                "current_patient_program_flow", None
            ),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        context.update(check_privileges(req, privileges_required))
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
            Concepts.ADVERSE_EVENT_ACTION.value,
            Concepts.ADVERSE_EVENT_ACTION_2.value,
            Concepts.ADVERSE_EVENT_ACTION_3.value,
            Concepts.ADVERSE_EVENT_ACTION_4.value,
            Concepts.ADVERSE_EVENT_ACTION_5.value,
            Concepts.ADVERSE_EVENT_OUTCOME.value,
            Concepts.DRUG_RECHALLENGE.value,
        ]
        form = fu.get_ae_by_uuid(req, formid)
        concepts = fu.remove_ae_duplicates(
            fu.get_form_concepts(adverse_event_concepts, req), form
        )
        if form:
            context["form"] = form
            context["concepts"] = concepts
            mu.add_url_to_breadcrumb(req, context["title"])
            return render(
                req, "app/tbregister/mdr/adverse_events.html", context=context
            )
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("editadverseevents", uuid=patientid, formid=formid)


def render_delete_adverse_events_form(req, formid):
    try:
        status, _ = ru.delete(req, f"mdrtb/adverseevents/{formid}")
        if status:
            messages.success(req, "Form deleted successfully")
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return redirect(req.session["redirect_url"], permanent=True)


def render_drug_resistence_form(req, patientid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_drug_resistence_form(req, patientid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
                return redirect(req.session["redirect_url"], permanent=True)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("drugresistanse", patientid=patientid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        drug_resistance_concepts = [Concepts.DRUG_RESISTANCE_DURING_TREATMENT.value]
        title = mu.get_global_msgs("mdrtb.drdt", locale=req.session["locale"])
        context = {
            "title": title,
            "concepts": fu.get_form_concepts(drug_resistance_concepts, req),
            "patient_id": patientid,
        }
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/mdr/drug_resistence.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("drugresistanse", uuid=patientid)


def render_edit_drug_resistence_form(req, patientid, formid):
    privileges_required = [Privileges.DELETE_ENCOUNTERS]
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_drug_resistence_form(
                req, patientid, req.POST, formid=formid
            )
            if response:
                messages.success(req, "Form updated successfully")
                return redirect(req.session["redirect_url"], permanent=True)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("editdrugresistanse", uuid=patientid, formid=formid)
    try:
        title = (
                mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                + " "
                + mu.get_global_msgs("mdrtb.drdt", locale=req.session["locale"])
        )
        context = {"title": title, "patient_id": patientid, "state": "edit"}
        context.update(check_privileges(req, privileges_required))
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        drug_resistance_concepts = [Concepts.DRUG_RESISTANCE_DURING_TREATMENT.value]
        form = fu.get_drug_resistance_form_by_uuid(req, formid)
        concepts = fu.remove_drug_resistance_duplicates(
            fu.get_form_concepts(drug_resistance_concepts, req), form
        )
        if form:
            context["form"] = form
            context["concepts"] = concepts
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/mdr/drug_resistence.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("editdrugresistanse", uuid=patientid, formid=formid)


def render_delete_drug_resistence_form(req, formid):
    try:
        status, _ = ru.delete(req, f"mdrtb/drugresistance/{formid}")
        if status:
            messages.success(req, "Form deleted successfully")
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return redirect(req.session.get("redirect_url"), permanent=True)


def render_regimen_form(req, patientid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_regimen_form(req, patientid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
                return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("regimen", uuid=patientid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        concept_ids = [
            Concepts.PLACE_OF_CENTRAL_COMMISSION.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.FUNDING_SOURCE.value,
            Concepts.SLD_REGIMEN_TYPE.value,
        ]
        title = mu.get_global_msgs("mdrtb.pv.regimenForm", locale=req.session["locale"])
        context = {
            "title": title,
            "concepts": fu.get_form_concepts(concept_ids, req),
            "current_patient_program_flow": req.session["current_patient_program_flow"],
        }
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/mdr/regimen.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("regimen", uuid=patientid)


def render_edit_regimen_form(req, patientid, formid):
    privileges_required = [Privileges.DELETE_ENCOUNTERS]
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_regimen_form(
                req, patientid, req.POST, formid=formid
            )
            if response:
                messages.success(req, "Form updated successfully")
                return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("editregimen", uuid=patientid, formid=formid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        concept_ids = [
            Concepts.PLACE_OF_CENTRAL_COMMISSION.value,
            Concepts.RESISTANCE_TYPE.value,
            Concepts.FUNDING_SOURCE.value,
            Concepts.SLD_REGIMEN_TYPE.value,
        ]
        form = fu.get_regimen_by_uuid(req, formid)
        title = (
                mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                + " "
                + mu.get_global_msgs("mdrtb.pv.regimenForm", locale=req.session["locale"])
        )
        context = {
            "title": title,
            "concepts": fu.remove_regimen_duplicates(
                fu.get_form_concepts(concept_ids, req), form
            ),
            "state": "edit",
            "current_patient_program_flow": req.session["current_patient_program_flow"],
        }
        context.update(check_privileges(req, privileges_required))
        if form:
            context["form"] = form
        else:
            raise Exception("Regimen form not found")
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/mdr/regimen.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session.get("redirect_url"))


def render_delete_regimen_form(req, formid):
    try:
        status, _ = ru.delete(req, f"mdrtb/regimen/{formid}")
        if status:
            messages.success(req, "Form deleted successfully")
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return redirect(req.session.get("redirect_url"))


def render_form_89(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_form89(req, uuid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
                return redirect(req.session["redirect_url"], permanent=True)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("form89", uuid=uuid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = mu.get_global_msgs("mdrtb.form89", locale=req.session["locale"])
        context = {
            "title": title,
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "patient": req.session["current_patient_program_flow"]["current_patient"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        form89_concepts = [
            Concepts.LOCATION_TYPE.value,
            Concepts.PREGNANT.value,
            Concepts.PROFESSION.value,
            Concepts.POPULATION_CATEGORY.value,
            Concepts.PLACE_OF_DETECTION.value,
            Concepts.CIRCUMSTANCES_OF_DETECTION.value,
            Concepts.METHOD_OF_DETECTION.value,
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.LOCATION_OF_EPTB.value,
            Concepts.LOCATION_OF_PTB.value,
            Concepts.PRESCRIBED_TREATMENT.value,
            Concepts.PLACE_OF_CENTRAL_COMMISSION.value,
        ]
        concepts = fu.get_form_concepts(form89_concepts, req)
        context["concepts"] = concepts
        # Attach TB03 form to autopopulate data if one exists
        tb03s = fu.get_patient_tb03_forms(req, uuid)
        if tb03s:
            context["tb03"] = tb03s[0]
        mu.add_url_to_breadcrumb(req, context["title"])
        patient = context["patient"]
        context["isEligibleForPregnancy"] = patient["age"] >= 15 and patient["age"] <= 49 and patient["gender"] == 'F'
        return render(req, "app/tbregister/dots/form89.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("form89", uuid=uuid)


def render_edit_form_89(req, uuid, formid):
    privileges_required = [Privileges.DELETE_ENCOUNTERS]
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_form89(req, uuid, req.POST, formid=formid)
            if response:
                messages.success(req, "Form updated successfully")
                return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("editform89", uuid=uuid, formid=formid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = (
                mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                + " "
                + mu.get_global_msgs("mdrtb.form89", locale=req.session["locale"])
        )
        context = {
            "title": title,
            "state": "edit",
            "uuid": uuid,
            "current_patient_program_flow": req.session["current_patient_program_flow"],
            "patient": req.session["current_patient_program_flow"]["current_patient"],
            "identifiers": pu.get_patient_identifiers(req, uuid),
            "constants": {
                "YES": Concepts.YES.value,
                "NO": Concepts.NO.value,
            },
        }
        context.update(check_privileges(req, privileges_required))
        form89_concepts = [
            Concepts.LOCATION_TYPE.value,
            Concepts.PREGNANT.value,
            Concepts.PROFESSION.value,
            Concepts.POPULATION_CATEGORY.value,
            Concepts.PLACE_OF_DETECTION.value,
            Concepts.CIRCUMSTANCES_OF_DETECTION.value,
            Concepts.METHOD_OF_DETECTION.value,
            Concepts.ANATOMICAL_SITE_OF_TB.value,
            Concepts.LOCATION_OF_PTB.value,
            Concepts.LOCATION_OF_EPTB.value,
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
            mu.add_url_to_breadcrumb(req, context["title"])
            return render(req, "app/tbregister/dots/form89.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("editform89", uuid=uuid, formid=formid)


def render_delete_form_89(req, formid):
    try:
        ru.delete(req, f"mdrtb/form89/{formid}")
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return redirect(req.session["redirect_url"])


def render_user_profile(req):
    if not check_if_session_alive(req):
        return redirect("login")
    title = mu.get_global_msgs(
        "Navigation.options", locale=req.session["locale"], source="OpenMRS"
    )
    context = {"title": title}
    if req.method == "POST":
        try:
            user_properties = req.session["logged_user"]["user"]["userProperties"]
            req.session["locale"] = req.POST["locale"]
            cache.delete("concepts")
            mu.get_all_concepts(req)
            user_properties["defaultLocale"] = (
                req.POST["locale"] if "locale" in req.POST else ""
            )
            user_properties["defaultLocation"] = (
                req.POST["district"]
                if "facility" not in req.POST
                else req.POST["facility"]
            )
            user_properties["proficientLocales"] = (
                req.POST["proficient_locales"]
                if "proficient_locales" in req.POST
                else ""
            )
            logged_in_user_uuid = req.session["logged_user"]["user"]["uuid"]
            _, _ = ru.post(
                req,
                f"user/{logged_in_user_uuid}",
                {"userProperties": user_properties},
            )
            return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect(req.session["redirect_url"])
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        user_properties = req.session["logged_user"]["user"]["userProperties"]
        default_locale = req.session["locale"]
        app_locales = ["en", "en_GB", "ru", "tj"]
        if default_locale in app_locales:
            app_locales.remove(default_locale)
        allowed_locales_openmrs = [
            locale.strip()
            for locale in mu.get_global_properties(req, "locale.allowed.list").split(
                ","
            )
        ]
        status, person = ru.get(
            req,
            "person/{}".format(req.session["logged_user"]["user"]["person"]["uuid"]),
            {"v": "full"},
        )
        if status:
            context["person"] = person
        context["allowed_locales_openmrs"] = [
            {"name": Constants[locale.upper()].value, "value": locale}
            for locale in allowed_locales_openmrs
        ]
        context["app_locales"] = [
            {"name": Constants[locale.upper()].value, "value": locale}
            for locale in app_locales
        ]
        context["default_locale"] = {
            "name": Constants[default_locale.upper()].value,
            "value": default_locale,
        }
        if "defaultLocation" in user_properties:
            if len(user_properties["defaultLocation"]) > 0:
                context["default_location"] = mu.get_location(
                    req,
                    user_properties["defaultLocation"],
                )
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/user_profile.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_transferout_form(req, patientuuid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_tranfer_out_form(req, patientuuid, req.POST)
            if response:
                messages.success(req, "Form created successfully")
                return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("transferout", uuid=patientuuid)
    else:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = mu.get_global_msgs("mdrtb.transferOut", locale=req.session["locale"])
        context = {"title": title, "patientuuid": patientuuid}
        mu.add_url_to_breadcrumb(req, context["title"])
        return render(req, "app/tbregister/dots/transfer.html", context=context)


def render_edit_transferout_form(req, patientuuid, formid):
    privileges_required = [Privileges.DELETE_ENCOUNTERS]
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        try:
            response = fu.create_update_tranfer_out_form(
                req, patientuuid, req.POST, formid=formid
            )
            if response:
                messages.success(req, "Form updated successfully")
                return redirect(req.session["redirect_url"])
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("edittransferout", uuid=patientuuid, formid=formid)
    try:
        form = fu.get_transfer_out_by_uuid(req, formid)
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        title = (
                mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                + " "
                + mu.get_global_msgs("mdrtb.transferOut", locale=req.session["locale"])
        )
        context = {
            "title": title,
            "patientuuid": patientuuid,
            "state": "edit",
        }
        context.update(check_privileges(req, privileges_required))
        mu.add_url_to_breadcrumb(req, context["title"])
        if form:
            context["form"] = form
        return render(req, "app/tbregister/dots/transfer.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("edittransferout", uuid=patientuuid, formid=formid)


def render_delete_transferout_form(req, formid):
    try:
        response = ru.delete(req, f"mdrtb/transferout/{formid}")
        if response:
            messages.warning(req, "Form deleted")
    except Exception as e:
        log_and_show_error(e, req)
    finally:
        return redirect(req.session["redirect_url"])


def render_logout(req):
    try:
        status, _ = ru.delete(req, "session")
        if status:
            ru.clear_session(req)
            return redirect("login")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session.get("redirect_url"))

def log_and_show_error(error, req):
    messages.error(req, error)
    logger.error(error, exc_info=True)


#########################
# Reporting Views START #
#########################
def render_report_form(req, target):
    if not check_if_session_alive(req):
        return redirect("login")
    title = util.get_report_name(target, req.session["locale"])
    context = {
        "title": title,
        "months": util.get_months(),
        "quarters": util.get_quarters(),
        "target": target,
    }
    req.session["redirect_url"] = req.META.get("HTTP_REFERER")
    if req.method == "POST":
        month = req.POST.get("month")
        end_month = req.POST.get("endmonth")
        quarter = req.POST.get("quarter")
        keys_to_check = ["facility", "district", "region"]
        location = None
        for key in keys_to_check:
            value = req.POST.get(key)
            if value and len(value) > 0:
                location = value
                break
        url = f"/{target}?"
        year = req.POST.get("year")
        if year:
            url += f"year={year}&"
        if location:
            url += f"location={location}&"
        if month:
            url += f"month={month}&month2={end_month}&"
        elif quarter:
            url += f"quarter={quarter}&"
        url += "a=1"
        print(url)
        return redirect(url)
    return render(req, "app/reporting/report_form_base.html", context)


def render_patient_list(req):
    if not check_if_session_alive(req):
        return redirect("login")
    title = mu.get_global_msgs("mdrtb.patientLists", locale=req.session["locale"])
    context = {
        "months": util.get_months(),
        "quarters": util.get_quarters(),
        "title": title,
    }
    try:
        if req.method == "POST":
            month = req.POST.get("month")
            quarter = req.POST.get("quarter")
            keys_to_check = ["facility", "district", "region"]
            location = None
            for key in keys_to_check:
                value = req.POST.get(key)
                if value and len(value) > 0:
                    location = value
                    break
            year = req.POST.get("year")
            listname = req.POST.get("listname")
            params = {"year": year, "listname": listname, "location": location}
            if month:
                params["month"] = month
                context["month"] = month
            elif quarter:
                params["quarter"] = quarter
                context["quarter"] = quarter
            status, response = ru.get(req, "mdrtb/patientlist", params)
            if status:
                context["year"] = year
                context["listname"] = util.get_patient_list_options(listname)
                context["location"] = lu.get_location_by_uuid(req, location)["name"]
                context["string_data"] = response["results"][0]["stringData"]
                return render(
                    req, "app/reporting/patientlist_report.html", context=context
                )
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("/")
    return render(req, "app/reporting/patientlist_report_form.html", context=context)


def render_tb03_report(req):
    context = {"title": "TB03 Report"}
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        month = req.GET.get("month", None)
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter", None)
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb03report", params)
        if status:
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["location"] = lu.get_single_location_hierarchy(
                mu.get_location(req, uuid=location, representation="FULL")
            )
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/tb03_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("searchPatientsView")


def render_tb03_single_report(req):
    context = {"title": "TB03 Report"}
    try:
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb03report", params)
        if status:
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/tb03_single_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("searchPatientsView")


def render_tb03u_single_report(req):
    context = {"title": "TB03u Single Report"}
    try:
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb03ureport", params)
        if status:
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["report_date"] = util.get_date_time_now()
            # Iterate over each patient dictionary in the context list
            for patient in context["patientSet"]:
                # remove spaces in drug names and convert to lower case
                patient['dstResults'] = {key.replace(' ', '').lower(): value for key, value in
                                         patient.get('dstResults', {}).items()}

            return render(req, "app/reporting/tb03u_single_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("searchPatientsView")


def render_tb03u_report(req):
    context = {"title": "TB03u Report"}
    try:
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb03ureport", params)
        if status:
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/tb03u_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("searchPatientsView")


def render_form89_report(req):
    context = {"title": "Form89 Report"}
    try:
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/form89report", params)
        if status:
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            return render(req, "app/reporting/form89_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("searchPatientsView")


def render_tb08_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "TB08 Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb08report", params)
        if status:
            # This line has to be added to every reporting view (render_<report_name>_report)
            # Not to the form views which has report_form in the end they are for generating report from form
            # This will default the location to Country if the location is null
            context["location"] = Constants.COUNTRY.value
            if location:
                context["location"] = mu.get_location(req, location)
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/tb08_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_tb08u_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "TB08u Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb08ureport", params)
        if status:
            context["location"] = Constants.COUNTRY.value
            if location:
                context["location"] = mu.get_location(req, location)
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/tb08u_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_tb07u_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "TB07u Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb07ureport", params)
        if status:
            context["location"] = Constants.COUNTRY.value
            if location:
                context["location"] = mu.get_location(req, location)
            context["patientSet"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/tb07u_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_tb07_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "TB07 Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month2"] = end_month
            params["month"] = month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb07report", params)
        if status:
            context["location"] = Constants.COUNTRY.value
            if location:
                context["location"] = mu.get_location(req, location)
            context["reporttime"] = datetime.datetime.today().strftime("%Y-%m-%d")
            context["table1"] = response["results"][0]
            context["json"] = json.dumps(response["results"][0])
            return render(req, "app/reporting/tb07_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_form8_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "Form8 Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/form8report", params)
        if status:
            context["location"] = Constants.COUNTRY.value
            if location:
                context["location"] = mu.get_location(req, location)
            context["form8data"] = response["results"][0]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/form8_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_missing_tb03_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "Missing TB03 Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb03missingreport", params)
        if status:
            context["location"] = Constants.COUNTRY.value
            if location:
                context["location"] = mu.get_location(req, location)
            missing_tb03_summary = response["results"][0]
            missing_tb03_data = response["results"][0]["dqItems"]
            for patient in missing_tb03_data:
                if patient:
                    patient_data = pu.get_patient(req, patient["patientUuid"])
                    if patient_data:
                        patient.update({"patient": patient_data})
            context["summary"] = missing_tb03_summary
            context["missingTB03"] = missing_tb03_data
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/missing_tb03_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_missing_tb03u_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "Missing TB03u Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/tb03umissingreport", params)
        if status:
            context["location"] = Constants.COUNTRY.value
            if location:
                context["location"] = mu.get_location(req, location)
            missing_tb03u_summary = response["results"][0]
            missing_tb03u_data = response["results"][0]["dqItems"]
            for patient in missing_tb03u_data:
                if patient:
                    patient_data = pu.get_patient(req, patient["patientUuid"])
                    if patient_data:
                        patient.update({"patient": patient_data})
            context["summary"] = missing_tb03u_summary
            context["missingTB03u"] = missing_tb03u_data
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/missing_tb03u_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_dotsdq_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "Dots Data Quality Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location, "type": "dots"}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/dataquality", params)
        if status:
            context["location"] = lu.get_single_location_hierarchy(
                mu.get_location(req, uuid=location, representation="FULL")
            )
            context["results"] = response["results"][0]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/dotsdq_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_mdrdq_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "MDRTB Data Quality Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location, "type": "mdrtb"}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/dataquality", params)
        if status:
            context["location"] = lu.get_single_location_hierarchy(
                mu.get_location(req, uuid=location, representation="FULL")
            )
            context["results"] = response["results"][0]
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/mdrdq_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_adverse_events_register_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "Adverse Events Register Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location, "type": "mdrtb"}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/adverseeventsregister", params)
        if status:
            context["location"] = lu.get_single_location_hierarchy(
                mu.get_location(req, uuid=location, representation="FULL")
            )
            context["forms"] = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            context["report_date"] = util.get_date_time_now()
            return render(
                req, "app/reporting/adverse_event_register_report.html", context
            )
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_quaterly_summary_ae_report(req):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER")
        context = {"title": "Adverse Events Register Report"}
        month = req.GET.get("month")
        end_month = req.GET.get("month2", None)
        quarter = req.GET.get("quarter")
        location = req.GET.get("location")
        year = req.GET.get("year")
        params = {"year": year, "location": location, "type": "mdrtb"}
        if month:
            params["month"] = month
            params["month2"] = end_month
        elif quarter:
            params["quarter"] = quarter
        status, response = ru.get(req, "mdrtb/adverseeventsquarterly", params)
        if status:
            context["location"] = lu.get_single_location_hierarchy(
                mu.get_location(req, uuid=location, representation="FULL")
            )
            tables = [
                {
                    key: value if value is not None else ""
                    for key, value in record.items()
                }
                for record in response["results"]
            ]
            tables_dict = {}
            for item in tables:
                for key, value in item.items():
                    tables_dict[key] = value
            context["tables"] = tables_dict
            context["report_date"] = util.get_date_time_now()
            return render(req, "app/reporting/quaterly_summary_ae_report.html", context)
        return redirect("searchPatientsView")
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_closed_reports(req, type):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs(
            "mdrtb.viewClosedReports", locale=req.session["locale"]
        ),
        "months": util.get_months(),
        "quarters": util.get_quarters(),
        "reports": util.get_report_names(type, req.session["locale"]),
        "type": type,
    }
    logged_in_user = req.session["logged_user"]["user"]["username"]
    if logged_in_user == "admin":
        context["unlock_privilege"] = True
        context["delete_privilege"] = True
    if req.method == "POST":
        try:
            params = {
                "year": req.POST["year"],
                "region": req.POST["region"],
            }
            if "report" in req.POST:
                params["name"] = req.POST["report"] if req.POST["report"] != "" else None
            if "quarter" in req.POST:
                params["quarter"] = req.POST["quarter"] if req.POST["quarter"] != "" else None
            elif "month" in req.POST:
                params["month"] = req.POST["month"] if req.POST["month"] != "" else None
            if "subregion" in req.POST and req.POST["subregion"]:
                params["subregion"] = req.POST["subregion"] if req.POST["subregion"] != "" else None
            if "district" in req.POST and req.POST["district"]:
                params["district"] = req.POST["district"] if req.POST["district"] != "" else None
            if "facility" in req.POST and req.POST["facility"]:
                params["facility"] = req.POST["facility"] if req.POST["facility"] != "" else None
            status, response = ru.get(req, "mdrtb/reportdata", params)
            if status and len(response["results"]) > 0:
                for report in response["results"]:
                    if report["location"]:
                        report["location"] = mu.get_location(
                            req, report["location"]["uuid"]
                        )
                context["report_data"] = response["results"]
                context["jsondata"] = json.dumps(response["results"])
            else:
                messages.info(req, "No saved reports found.")
        except Exception as e:
            log_and_show_error(e, req)
    return render(req, "app/reporting/closed_reports.html", context)


def render_single_closed_report(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {}
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        status, response = ru.get(req, f"mdrtb/reportdata/{uuid}", {})
        if status:
            context["title"] = response["reportName"]
            context["table_data"] = util.string_to_html(response["tableData"])
        return render(req, "app/reporting/single_closed_report.html", context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def save_closed_report(req):
    if req.method == "POST":
        try:
            overwrite_report = False
            location = lu.get_single_location_hierarchy(
                mu.get_location(req, uuid=req.POST["location"], representation="FULL")
            )
            year = req.POST["year"]
            report_name = req.POST["reportName"]
            params = {
                "year": year,
                "name": report_name,
                "region": location["region"]["uuid"],
            }
            if location["district"]:
                params["district"] = location["district"]["uuid"]
            if location["facility"]:
                params["facility"] = location["district"]["uuid"]
            if req.POST.get("month"):
                params["month"] = req.POST["month"]
            if req.POST.get("quarter"):
                params["quarter"] = req.POST["quarter"]

            _, exist_report = ru.get(
                req, "mdrtb/reportdata", parameters=params
            )
            report_to_overwrite = None
            if exist_report and len(exist_report.get("results", [])) > 0:
                for report in exist_report.get("results", []):
                    if report["reportStatus"] == "UNLOCKED" and report["reportName"] == report_name:
                        report_location = lu.get_single_location_hierarchy(
                            mu.get_location(req, uuid=report["location"]["uuid"], representation="FULL")
                        )
                        if (report_location["region"]["uuid"] == location["region"]["uuid"]
                                and (not report_location["district"]
                                or report_location["district"]["uuid"] == location["district"]["uuid"])
                                and (not report_location["facility"]
                                or report_location["facility"]["uuid"] == location["facility"]["uuid"])
                        ):
                            overwrite_report = True
                            report_to_overwrite = report["uuid"]
                            break
                    else:
                        raise Exception(
                            f"The {report['reportName']} with the following parameters already exists and is LOCKED"
                        )
            else:
                overwrite_report = True

            if overwrite_report:
                report_data = {
                    "year": year,
                    "location": req.POST["location"],
                    "reportName": report_name,
                    "tableData": str(req.POST["tableData"]),
                    "reportStatus": "UNLOCKED",
                    "reportType": req.POST["reportType"],
                }
                if req.POST.get("quarter"):
                    report_data["quarter"] = req.POST["quarter"]
                if req.POST.get("month"):
                    report_data["month"] = req.POST["month"]
                if report_to_overwrite is not None:
                    report_data["uuid"] = report_to_overwrite

                status, response = ru.post(req, "mdrtb/reportdata", data=report_data)
                if status:
                    return JsonResponse({"success": True})
                else:
                    raise Exception("Failed to save report")
            else:
                raise Exception(
                    f"The {report_name} with the following parameters already exists and is LOCKED"
                )
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("/")
    else:
        pass
#########################
# Reporting Views - END #
#########################


#########################
# CommonLab Views START #
#########################
def render_manage_test_types(req):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs(
            "commonlabtest.labtesttype.manage", locale=req.session["locale"]
        )
    }
    if req.method == "POST":
        try:
            search_results = cu.get_test_types_by_search(req, req.POST["search"])
            if len(search_results) > 0:
                context["response"] = search_results
                return render(
                    req, "app/commonlab/managetesttypes.html", context=context
                )
            else:
                status, response = ru.get(req, "commonlab/labtesttype", {"v": "full"})
                context["response"] = response["results"]
                return render(
                    req, "app/commonlab/managetesttypes.html", context=context
                )
        except Exception as e:
            log_and_show_error(e, req)
            return redirect(req.session["redirect_url"])
    try:
        status, response = ru.get(req, "commonlab/labtesttype", {"v": "full"})
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        mu.add_url_to_breadcrumb(req, context["title"])
        context["response"] = response["results"] if status else []
        return render(req, "app/commonlab/managetesttypes.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def fetch_attributes(req):
    if not check_if_session_alive(req):
        return redirect("login")
    response = cu.get_attributes_of_labtest(req, req.GET["uuid"])
    attributes = []
    for attribute in response:
        attributes.append(
            {
                "attrName": attribute["name"],
                "sortWeight": attribute["sortWeight"],
                "groupName": "None"
                if "groupName" not in attribute
                else attribute["groupName"],
                "multisetName": "None"
                if "groupName" not in attribute
                else attribute["multisetName"],
            }
        )
    return JsonResponse({"attributes": attributes})


def render_add_test_type(req):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs(
            "commonlabtest.labtesttype.add", locale=req.session["locale"]
        )
    }
    if req.method == "POST":
        body = {
            "name": req.POST["testname"],
            "testGroup": req.POST["testgroup"],
            "requiresSpecimen": True if req.POST["requirespecimen"] == "Yes" else False,
            "referenceConcept": req.POST["referenceConceptuuid"],
            "description": req.POST["description"],
            "shortName": None if req.POST["shortname"] == "" else req.POST["shortname"],
        }
        status, response = cu.add_edit_test_type(req, body, "commonlab/labtesttype")
        if status:
            return redirect("managetesttypes")
        else:
            context["error"] = response
            return render(req, "app/commonlab/addtesttypes.html", context=context)
    context["testGroups"] = cu.get_commonlab_test_groups()
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    mu.add_url_to_breadcrumb(req, context["title"])
    return render(req, "app/commonlab/addtesttypes.html", context=context)


def render_edit_test_type(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs(
            "commonlabtest.labtesttype.edit", locale=req.session["locale"]
        )
    }
    status, response = ru.get(
        req, f"commonlab/labtesttype/{uuid}", {"v": "full", "lang": "en"}
    )
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    mu.add_url_to_breadcrumb(req, context["title"])
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
        # context["referenceConcepts"] = cu.get_commonlab_concepts_by_type(
        #     req, "labtesttype"
        # )
        context["testGroups"] = util.remove_given_str_from_arr(
            cu.get_commonlab_test_groups(), data["testGroup"]
        )
    if req.method == "POST":
        body = {
            "name": req.POST["testname"],
            "testGroup": req.POST["testgroup"],
            "requiresSpecimen": True if req.POST["requirespecimen"] == "Yes" else False,
            "referenceConcept": req.POST["referenceConceptuuid"],
            "description": req.POST["description"],
            "shortName": None if req.POST["shortname"] == "" else req.POST["shortname"],
        }
        status, response = cu.add_edit_test_type(
            req, body, f"commonlab/labtesttype/{uuid}"
        )
        if status:
            return redirect("managetesttypes")
    return render(req, "app/commonlab/addtesttypes.html", context=context)


def render_retire_test_type(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    if req.method == "POST":
        status, _ = ru.delete(req, f"commonlab/labtesttype/{uuid}")
        if status:
            return redirect("managetesttypes")
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    return render(req, "app/commonlab/addtesttypes.html")


def render_manage_attributes(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {"labTestUuid": uuid, "title": "Manage Attributes"}
    response = cu.get_attributes_of_labtest(req, uuid)
    context["attributes"] = response
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    mu.add_url_to_breadcrumb(req, context["title"])
    return render(req, "app/commonlab/manageattributes.html", context=context)


def render_addattributes(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "labTestUuid": uuid,
        "prefferedHandlers": cu.get_preffered_handler(),
        "dataTypes": cu.get_attributes_data_types(),
        "title": mu.get_global_msgs(
            "commonlabtest.labtestattributetype.add", locale=req.session["locale"]
        ),
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
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    mu.add_url_to_breadcrumb(req, context["title"])
    return render(req, "app/commonlab/addattributes.html", context=context)


def render_edit_attribute(req, testid, attrid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "state": "edit",
        "testid": testid,
        "title": mu.get_global_msgs(
            "commonlabtest.labtestattributetype.edit", locale=req.session["locale"]
        ),
    }
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    mu.add_url_to_breadcrumb(req, context["title"])
    status, response = ru.get(
        req, f"commonlab/labtestattributetype/{attrid}", {"v": "full"}
    )
    if status:
        context["attribute"] = cu.get_custom_attribute(
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
    return render(req, "app/commonlab/addattributes.html", context=context)


def render_managetestorders(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    try:
        context = {
            "title": mu.get_global_msgs(
                "commonlabtest.labtest.manage", locale=req.session["locale"]
            ),
            "patient": uuid,
        }
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        mu.add_url_to_breadcrumb(req, context["title"])
        status, response = ru.get(
            req,
            f"commonlab/labtestorder",
            {
                "patient": uuid,
                "v": "custom:(uuid,labTestType,labReferenceNumber,order,auditInfo,labTestSamples)",
            },
        )
        if status:
            _, lab_test_types = ru.get(req, "commonlab/labtesttype", {"v": "full"})
            for lab_result in response["results"]:
                attributes = cu.get_labtest_attributes(req, lab_result["uuid"])
                lab_result.update({"attributes": attributes})
                if lab_test_types:
                    for ltt in lab_test_types["results"]:
                        if ltt["uuid"] == lab_result["labTestType"]["uuid"]:
                            lab_result.update({"labTestType": ltt})
            orders = response["results"]
            for order in orders:
                sample_accepted = check_if_sample_exists(req, order["uuid"])
                order.update({"sample_accepted": sample_accepted})
            context["orders"] = response["results"]
            context["json_orders"] = json.dumps(response["results"])
        patient = pu.get_patient(req, uuid)
        if patient:
            context["patientdata"] = patient
        return render(req, "app/commonlab/managetestorders.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect(req.session["redirect_url"])


def render_add_lab_test(req, uuid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs(
            "commonlabtest.labtest.add", locale=req.session["locale"]
        ),
        "patient": uuid,
    }
    patient = pu.get_patient(req, uuid)
    if patient:
        context["patientdata"] = patient
    if req.method == "POST":
        create = req.POST.get("createencounter")
        encounter = None
        if create:
            encounter_datetime = util.iso_to_normal(util.get_date_time_now(), tajik=False)
            encounter_body = {
              "encounterDatetime": encounter_datetime,
              "encounterType": EncounterType.SPECIMEN_COLLECTION.value,
              "patient": uuid,
              "encounterProviders": [
                {
                  "provider": req.session["logged_user"]["currentProvider"]["uuid"],
                  "encounterRole": Constants.ENCOUNTER_ROLE_UNKNOWN.value
                }
              ],
              "obs": [
                  {
                      "person": uuid,
                      "concept": Concepts.MONTH_OF_TREATMENT.value,
                      "obsDatetime": encounter_datetime,
                      "value": 0
                  }
              ]
            }
            status, response = ru.post(req, "encounter", encounter_body)
            if status:
                encounter = response["uuid"]
        else:
            encounter = req.POST["encounter"]
        try:
            body = {
                "labTestType": req.POST["testType"],
                "labReferenceNumber": req.POST["labref"],
                "order": {
                    "patient": uuid,
                    "concept": cu.get_reference_concept_of_labtesttype(
                        req, req.POST["testType"]
                    ),
                    "encounter": encounter,
                    "type": "order",
                    "instructions": None
                    if "instructions" not in req.POST
                    else req.POST["instructions"],
                    "orderType": Constants.TEST_ORDER.value,
                    "orderer": req.session["logged_user"]["currentProvider"]["uuid"],
                    "careSetting": req.POST["careSetting"],
                },
            }
            status, response = ru.post(req, "commonlab/labtestorder", body)
            if status:
                return redirect("managetestorders", uuid=uuid)
            else:
                log_and_show_error(response["error"]["message"], req)
                return redirect("managetestorders", uuid=uuid)
        except Exception as e:
            log_and_show_error(e, req)
            return redirect("addlabtest", uuid=uuid)

    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        mu.add_url_to_breadcrumb(req, context["title"])
        encounters = pu.get_patient_encounters(req, uuid)
        labtests, testgroups = cu.get_test_groups_and_tests(req)
        if encounters:
            context["encounters"] = encounters["results"]
            context["testgroups"] = list(dict.fromkeys(testgroups))
            context["labtests"] = json.dumps(labtests)
            context["care_setting"] = {
                "inpatient": {
                    "name": Constants.INPATIENT.name.title(),
                    "value": Constants.INPATIENT.value,
                },
                "outpatient": {
                    "name": Constants.OUTPATIENT.name.title(),
                    "value": Constants.OUTPATIENT.value,
                },
            }
        return render(req, "app/commonlab/addlabtest.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("addlabtest", uuid=uuid)


def render_edit_lab_test(req, patientid, orderid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs(
            "commonlabtest.order.edit", locale=req.session["locale"]
        ),
        "state": "edit",
        "orderid": orderid,
        "patientid": patientid,
    }
    patient = pu.get_patient(req, patientid)
    if patient:
        context["patientdata"] = patient
    try:
        if req.method == "POST":
            body = {
                "labTestType": req.POST["testType"],
                "labReferenceNumber": req.POST["labref"],
                "order": {
                    "patient": patientid,
                    "concept": cu.get_reference_concept_of_labtesttype(
                        req, req.POST["testType"]
                    ),
                    "encounter": req.POST["encounter"],
                    "type": "order",
                    "instructions": None
                    if "instructions" not in req.POST
                    else req.POST["instructions"],
                    "orderer": req.session["logged_user"]["currentProvider"]["uuid"],
                    "careSetting": req.POST["careSetting"],
                },
            }
            status, response = ru.post(req, f"commonlab/labtestorder/{orderid}", body)
            if status:
                return redirect("managetestorders", uuid=patientid)
            else:
                log_and_show_error("Error creating test order", req)
                return render(req, "app/commonlab/addlabtest.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("editlabtest", uuid=patientid, orderid=orderid)
    try:
        status, response = ru.get(
            req,
            f"commonlab/labtestorder/{orderid}",
            {"v": "full"},
        )
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        mu.add_url_to_breadcrumb(req, context["title"])
        if status:
            encounters = pu.get_patient_encounters(
                req, response["order"]["patient"]["uuid"]
            )
            labtests, testgroups = cu.get_test_groups_and_tests(req)
            context["laborder"] = cu.get_custom_lab_order(response)
            context["encounters"] = util.remove_obj_from_objarr(
                encounters["results"],
                context["laborder"]["order"]["encounter"]["uuid"],
                "uuid",
            )
            testgroups = list(dict.fromkeys(testgroups))
            context["testgroups"] = util.remove_given_str_from_arr(
                testgroups, context["laborder"]["labtesttype"]["testGroup"]
            )
            context["labtests"] = json.dumps(labtests)
            context["care_setting"] = {
                "inpatient": {
                    "name": Constants.INPATIENT.name.title(),
                    "value": Constants.INPATIENT.value,
                },
                "outpatient": {
                    "name": Constants.OUTPATIENT.name.title(),
                    "value": Constants.OUTPATIENT.value,
                },
            }
            return render(req, "app/commonlab/addlabtest.html", context=context)
        else:
            log_and_show_error("Error getting lab test", req)
            return redirect("managetestorders", uuid=patientid)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("editlabtest", uuid=patientid, orderid=orderid)


def render_delete_lab_test(req, patientid, orderid):
    if not check_if_session_alive(req):
        return redirect("login")
    status, response = ru.delete(req, f"commonlab/labtestorder/{orderid}")
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    if status:
        return redirect("managetestorders", uuid=patientid)


def render_managetestsamples(req, orderid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs(
            "commonlabtest.labtestsample.manage", locale=req.session["locale"]
        ),
        "orderid": orderid,
    }
    status, response = ru.get(
        req, f"commonlab/labtestorder/{orderid}", {"v": "custom:(labTestSamples,order:(uuid,patient:(uuid))"}
    )
    req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
    mu.add_url_to_breadcrumb(req, context["title"])
    if status:
        context["samples"] = response["labTestSamples"]
        patientid = response["order"]["patient"]["uuid"]
        patient = pu.get_patient(req, patientid)
        if patient:
            context["patientdata"] = patient
    context["sitecodes"] = lu.get_location_site_codes(req)
    return render(req, "app/commonlab/managetestsamples.html", context=context)


def render_add_test_sample(req, orderid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs("mdrtb.add", locale=req.session["locale"])
                 + mu.get_global_msgs("mdrtb.sample", locale=req.session["locale"]),
        "orderid": orderid,
    }
    if req.method == "POST":
        body = {
            "labTest": orderid,
            "specimenType": req.POST["specimentype"],
            "specimenSite": req.POST["specimensite"],
            "sampleIdentifier": req.POST["specimenid"],
            "collectionDate": req.POST["collectedon"],
            "status": "COLLECTED",
            "collector": req.session["logged_user"]["currentProvider"]["uuid"],
        }
        if "quantity" in req.POST and req.POST["quantity"]:
            body["quantity"] = req.POST["quantity"]
        if "units" in req.POST and req.POST["units"]:
            body["units"] = req.POST["units"]
        status, response = ru.post(req, "commonlab/labtestsample", body)
        if status:
            return redirect("managetestsamples", orderid=orderid)
        else:
            log_and_show_error("Error adding samples", req)
            return redirect("addtestsample", orderid=orderid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        mu.add_url_to_breadcrumb(req, context["title"])
        context["specimentype"] = cu.get_commonlab_concepts_by_type(
            req, "commonlabtest.specimenTypeConceptUuid"
        )
        context["specimensite"] = cu.get_commonlab_concepts_by_type(
            req, "commonlabtest.specimenSiteConceptUuid"
        )
        context["units"] = cu.get_sample_units(req)
        return render(req, "app/commonlab/addsample.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("addtestsample", orderid=orderid)


def render_edit_test_sample(req, orderid, sampleid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs("mdrtb.edit", locale=req.session["locale"])
                 + mu.get_global_msgs("mdrtb.sample", locale=req.session["locale"]),
        "orderid": orderid,
        "sampleid": sampleid,
        "state": "edit",
    }
    if req.method == "POST":
        body = {
            "labTest": orderid,
            "specimenType": req.POST["specimentype"],
            "specimenSite": req.POST["specimensite"],
            "sampleIdentifier": req.POST["specimenid"],
            "quantity": "" if "quantity" not in req.POST else req.POST["quantity"],
            "units": "" if "units" not in req.POST else req.POST["units"],
            "collectionDate": req.POST["collectedon"],
            "status": "COLLECTED",
            "collector": req.session["logged_user"]["currentProvider"]["uuid"],
        }
        status, response = ru.post(req, f"commonlab/labtestsample/{sampleid}", body)
        if status:
            return redirect("managetestsamples", orderid=orderid)
        else:
            log_and_show_error("Error adding samples", req)
            return redirect("edittestsample", orderid=orderid, sampleid=sampleid)
    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        mu.add_url_to_breadcrumb(req, context["title"])
        status, response = ru.get(
            req, f"commonlab/labtestsample/{sampleid}", {"v": "full"}
        )
        if status:
            sample = response
            specimen_type = cu.get_commonlab_concepts_by_type(
                req, "commonlabtest.specimenTypeConceptUuid"
            )
            specimen_site = cu.get_commonlab_concepts_by_type(
                req, "commonlabtest.specimenSiteConceptUuid"
            )
            context["specimentype"] = util.remove_obj_from_objarr(
                specimen_type, sample["specimenType"]["uuid"], "uuid"
            )
            context["specimensite"] = util.remove_obj_from_objarr(
                specimen_site, sample["specimenSite"]["uuid"], "uuid"
            )
            units = cu.get_sample_units(req)
            context["units"] = util.remove_obj_from_objarr(
                units, sample["units"], "uuid"
            )
            context["sample"] = sample
            # context["sample"] = response
            return render(req, "app/commonlab/addsample.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("edittestsample", orderid=orderid, sampleid=sampleid)


def render_change_sample_status(req, orderid, sampleid):
    statuses = {"Accept": "ACCEPTED", "Reject": "REJECTED"}
    if req.method == "POST":
        sample_status = statuses[req.POST["status"]]
        try:
            status, _ = ru.post(
                req, f"commonlab/labtestsample/{sampleid}", {"status": sample_status}
            )
            if status:
                if sample_status == "ACCEPTED":
                    messages.success(req, f"Sample {sample_status}")
                else:
                    messages.warning(req, f"Sample {sample_status}")
        except Exception:
            log_and_show_error(f"Sample {sample_status}", req)
    return redirect("managetestsamples", orderid=orderid)


def render_delete_sample(req, orderid, sampleid):
    if not check_if_session_alive(req):
        return redirect("login")
    status, reponse = ru.delete(req, f"commonlab/labtestsample/{sampleid}")
    if status:
        return redirect(req.session["redirect_url"])


def render_add_test_results(req, orderid):
    if not check_if_session_alive(req):
        return redirect("login")
    context = {
        "title": mu.get_global_msgs("mdrtb.addTestResults", locale=req.session["locale"]),
        "orderid": orderid,
    }
    if req.method == "POST":
        status, laborder = ru.get(req, f"commonlab/labtestorder/{orderid}", {})
        if status:
            body = {
                "order": laborder["order"]["uuid"],
                "labReferenceNumber": laborder["labReferenceNumber"],
                "labTestType": laborder["labTestType"]["uuid"],
                "attributes": [],
            }
            for key, value in req.POST.items():
                if key in ("csrfmiddlewaretoken", "state") or not value:
                    continue
                obj = {
                    "labTest": laborder["uuid"],
                    "attributeType": key,
                    "valueReference": value,
                }
                if req.POST.get("state"):
                    for attribute in laborder["attributes"]:
                        if attribute["attributeType"]["uuid"] == key:
                            obj["uuid"] = attribute["uuid"]
                body["attributes"].append(obj)
            try:
                status, response = ru.post(
                    req, f"commonlab/labtestorder/{orderid}", body
                )
                if status:
                    return redirect(req.session["redirect_url"])
            except Exception as e:
                log_and_show_error(e, req)
                return redirect("addtestresults", orderid=orderid)
        else:
            log_and_show_error("Error creating the results", req)
            return redirect("addtestresults", orderid=orderid)

    try:
        req.session["redirect_url"] = req.META.get("HTTP_REFERER", "/")
        mu.add_url_to_breadcrumb(req, context["title"])
        status, response = ru.get(
            req,
            f"commonlab/labtestorder/{orderid}",
            {"v": "custom:(attributes,auditInfo,labReferenceNumber,labTestSamples)"},
        )
        if status:
            context["labAuditInfo"] = response["auditInfo"]
            context["labReferenceNumber"] = response["labReferenceNumber"]
            for sample in response["labTestSamples"]:
                if sample["status"] in [Constants.ACCEPTED.value, Constants.PROCESSED.value]:
                    context["labSample"] = sample
                    break

            if len(response["attributes"]) > 0:
                context["state"] = "edit"
                attributes = cu.get_labtest_attributes(req, orderid, representation="FULL")
            else:
                attributes = cu.get_custom_attribute_for_labresults(req, orderid)
            context["labAttributes"] = attributes
            # Separate out common attributes from groups
            common = []
            grouped = {}
            for attribute in attributes:
                if attribute["attributeType"]["group"]:
                    group = attribute["attributeType"]["group"]
                    if group not in grouped:
                        grouped[group] = []  # Initialize an empty list for the group if it doesn't exist
                    grouped[group].append(attribute)
                else:
                    common.append(attribute)
            context["labCommonAttributes"] = common
            context["labGroupedAttributes"] = grouped
            context["sample"] = context["labSample"]
            return render(req, "app/commonlab/addtestresults.html", context=context)
    except Exception as e:
        log_and_show_error(e, req)
        return redirect("addtestresults", orderid=orderid)


def check_if_sample_exists(req, orderid):
    sample_accepted = False
    try:
        status, response = ru.get(
            req, f"commonlab/labtestorder/{orderid}", {"v": "custom:(labTestSamples)"}
        )
        if status:
            if len(response["labTestSamples"]) > 0:
                for sample in response["labTestSamples"]:
                    if sample["status"] in [
                        Constants.ACCEPTED.value,
                        Constants.PROCESSED.value,
                    ]:
                        sample_accepted = True
                        break
            return sample_accepted
    except Exception:
        log_and_show_error("Error fetching Samples", req)
        return sample_accepted


def submit_order_to_lab(req, orderid):
    if req.method == "POST":
        try:
            fields = ("custom:(uuid,labTestType,labReferenceNumber,"
                      "order:(uuid,patient:(uuid),orderer,"
                      "encounter:(uuid,encounterDatetime,encounterType)))")
            status, order = ru.get(req,
                f"commonlab/labtestorder/{orderid}",
                {"v": fields})
            accepted_sample = req.POST.get("accepted_sample")
            if status:
                patient_uuid = order["order"]["patient"]["uuid"]
                patient = pu.get_patient(req, patient_uuid)
                status, sample = ru.get(
                    req, f"commonlab/labtestsample/{accepted_sample}", {"v": "full"}
                )

            ngendercode = 1 if patient["gender"] == 'M' else 2
            sexternalorderid = order["labReferenceNumber"]
            sexternalsampleid = sample["sampleIdentifier"]
            sfirstname = patient["givenName"]
            slastname = patient["familyName"]
            sdob = patient["dob"]
            sdistrictname = patient["countyDistrict"]
            scountryname = Constants.COUNTRY.value
            scityname = patient["cityVillage"] if patient["cityVillage"] else ""
            dcollectiondate = util.iso_to_normal(sample["collectionDate"], False)
            ssubmitterfirstname = order["order"]["orderer"]["identifier"]
            sinstitutionname = "NTP"
            ssitecode = req.POST.get("site_code")
            sordertestcomment = sample["comments"]

            # Select the identifier based on the Encounter type selected:
                # For Suspect, select Suspect ID
                # For TB03 or Form89, select DOTS ID
                # Otherwise select MDR-TB ID
            encounter_type = order["order"]["encounter"]["encounterType"]["uuid"]
            if encounter_type == EncounterType.TB03.value or encounter_type == EncounterType.FROM_89.value:
                identifier_type = Constants.DOTS_IDENTIFIER.value
            elif encounter_type in (EncounterType.TB03u_MDR.value, EncounterType.ADVERSE_EVENT.value, EncounterType.RESISTANCE_DURING_TREATMENT.value):
                identifier_type = Constants.MDR_IDENTIFIER.value
            else:
                identifier_type = Constants.SUSPECT_IDENTIFIER.value
            for identifier in patient["identifiers"]:
                if identifier["identifierType"]["uuid"] == identifier_type:
                    spatientrefid = identifier["identifier"]
            # If no identifier was chosen, then pick the first one
            if not spatientrefid:
                spatientrefid = patient["identifiers"][0]

            sposttemplate = ""
            try:
                obj = {
                        "order": order["order"]["uuid"],
                        "labReferenceNumber": sexternalorderid,
                        "labTestType": Constants.COMMON_TEST.value,
                        "attributes": [
                            {
                                "labTest": orderid,
                                "attributeType": "001aaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                                "valueReference": dcollectiondate
                            },
                            {
                                "labTest": orderid,
                                "attributeType": "013aaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                                "valueReference": sexternalsampleid
                            },
                        ]
                    }
                sposttemplate = json.dumps(obj)
            except:
                pass

            data = {
                "externalorder": {
                    "ngendercode": ngendercode,
                    "sexternalorderid": sexternalorderid,
                    "sexternalsampleid": sexternalsampleid,
                    "sfirstname": sfirstname,
                    "slastname": slastname,
                    "sdob": sdob,
                    "spatientrefid": spatientrefid,
                    "sdistrictname": sdistrictname,
                    "scountryname": scountryname,
                    "scityname": scityname if scityname else "",
                    "dcollectiondate": dcollectiondate,
                    "ssubmitterfirstname": ssubmitterfirstname if ssubmitterfirstname else "",
                    "sinstitutionname": sinstitutionname,
                    "ssitecode": ssitecode,
                    "sordertestcomment": sordertestcomment if sordertestcomment else "",
                    "extras": {
                        "spostlink": f"{REST_API_BASE_URL}commonlab/labtestorder/{orderid}",
                        "sorder": order["order"]["uuid"],
                        "spatient": order["order"]["patient"]["uuid"],
                        "slabtesttype": Constants.COMMON_TEST.value,
                        "slabtest": orderid,
                        "sposttemplate": sposttemplate
                    }
                }
            }
            # Try with all the extra attribute attached
            try:
                status = ru.post_lab_order(data=data)
            except:
                # In case of exception, try without
                data["externalorder"].pop("extras", None)  # Remove the 'extras' attribute
                status = ru.post_lab_order(data=data)
            if status == 201 or status == 200:
                message = mu.get_global_msgs("qualis.message.success", locale=req.session["locale"])
            else:
                message = mu.get_global_msgs("qualis.message.error", locale=req.session["locale"])
            messages.success(req, f"{message}")
        except Exception as ex:
            message = mu.get_global_msgs("qualis.message.duplicate", locale=req.session["locale"])
            error_message = f"Error! {ex}: {message}"
            log_and_show_error(error_message, req)
    return redirect("managetestsamples", orderid=orderid)

#######################
# CommonLab Views END #
#######################
