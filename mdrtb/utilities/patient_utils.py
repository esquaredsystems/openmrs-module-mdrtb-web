from utilities import common_utils as u
from utilities import restapi_utils as ru
from utilities import metadata_util as mu
from utilities import forms_util as fu
from utilities import commonlab_util as cu
from resources.enums.constants import Constants
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.encounterType import EncounterType
import logging

logger = logging.getLogger("django")


def get_patient(req, uuid):
    """
    Retrieves patient information by UUID.

    Parameters:
        req (Request): The request object.
        uuid (str): The UUID of the patient.

    Returns:
        dict or None: A dictionary containing patient information if the patient is found, None otherwise.

    Note:
        The function makes a request to retrieve the patient data and extracts relevant information such as UUID, name,
        age, date of birth, gender, address, identifiers, and audit information.
    """
    patient = {}
    status, patient_data = ru.get(req, f"patient/{uuid}", {"v": "full"})
    if status:
        patient["uuid"] = uuid
        patient["name"] = patient_data["person"]["display"]
        patient["age"] = patient_data["person"]["age"]
        patient["dob"] = patient_data["person"]["birthdate"]
        patient["gender"] = patient_data["person"]["gender"]
        patient["address"] = patient_data["person"]["preferredAddress"]["display"]
        patient["identifiers"] = patient_data["identifiers"]
        patient["auditInfo"] = patient_data["auditInfo"]
        return patient
    else:
        return None


def get_patient_encounters(req, uuid):
    """
    Retrieves the encounters for a specific patient.

    Parameters:
        req (object): The request object for making API calls.
        uuid (str): The UUID of the patient.

    Returns:
        dict or None: The response containing the encounters if successful, or None if unsuccessful.

    """
    status, response = ru.get(req, "encounter", {"patient": uuid})
    if status:
        return response
    else:
        return None


def create_patient(req, data):
    """
    Creates a new patient with the provided data.

    Parameters:
        req (Request): The request object.
        data (dict): The data for creating the patient. It should contain the following fields:
            - patientidentifier (str): The patient's identifier.
            - patientidentifiertype (str): The type of the patient identifier.
            - district (str): The location of the patient (district or facility).
            - givenname (str): The patient's given name.
            - familyname (str): The patient's family name.
            - gender (str): The patient's gender.
            - address (str): The patient's address.
            - region (str): The patient's region/state/province.
            - country (str): The patient's country.
            - dob (str, optional): The patient's date of birth (YYYY-MM-DD).
            - age (int, optional): The patient's age.
            - deceased (bool, optional): Indicates if the patient is deceased.
            - deathdate (str, optional): The patient's date of death (YYYY-MM-DD).
            - causeofdeath (str, optional): The cause of the patient's death.
            - voided (bool, optional): Indicates if the patient is voided.
            - reasontovoid (str, optional): The reason for voiding the patient.

    Returns:
        tuple: A tuple containing the status (bool) indicating if the patient creation was successful and the response (dict)
        containing the created patient information if successful, or an exception if an error occurred during the creation process.
    """

    patient_info = {
        "identifiers": [
            {
                "identifier": data["patientidentifier"],
                "identifierType": data["patientidentifiertype"],
                "location": data["district"]
                if "facility" not in data
                else data["facility"],
            }
        ],
        "person": {
            "names": [
                {"givenName": data["givenname"], "familyName": data["familyname"]}
            ],
            "gender": data["gender"],
            "addresses": [
                {
                    "address1": data["address"],
                    "stateProvince": data["region"],
                    "country": data["country"],
                }
            ],
        },
    }
    if "dob" in data:
        patient_info["person"]["birthdate"] = data["dob"]
        patient_info["person"]["birthdateEstimated"] = False
    else:
        patient_info["person"]["age"] = data["age"]

    if "deceased" in data:
        patient_info["person"]["deathDate"] = data["deathdate"]
        patient_info["person"]["causeOfDeath"] = data["causeofdeath"]
    else:
        patient_info["person"]["deathDate"] = None
        patient_info["person"]["dead"] = False
        patient_info["person"]["causeOfDeath"] = None

    if "voided" in data:
        patient_info["person"]["reasonToVoid"] = data["reasontovoid"]

    try:
        status, response = ru.post(req, "patient", patient_info)
        if status:
            location_enrolled_in = data.get(
                "facility", data.get("district", data.get("region", None))
            )
            if location_enrolled_in:
                req.session["location_enrolled_in"] = mu.get_location(
                    req, location_enrolled_in, "FULL"
                )
            return status, response
    except Exception as e:
        raise Exception(str(e))


def get_patient_identifiers(req, patient_uuid):
    """
    Retrieves the identifiers associated with a patient.

    Parameters:
        req (Request): The request object.
        patient_uuid (str): The UUID of the patient.

    Returns:
        dict: A dictionary containing the patient identifiers. The keys represent the identifier types:
            - "dots" (dict): The DOTS identifier information, if available. It contains the following fields:
                - "type" (str): The UUID of the identifier type.
                - "identifier" (str): The DOTS identifier value.
                - "created_at" (str): The creation date of the identifier.
                - "location" (str): The UUID of the location associated with the identifier.
            - "mdr" (dict): The MDR identifier information, if available. It contains the following fields:
                - "type" (str): The UUID of the identifier type.
                - "identifier" (str): The MDR identifier value.
                - "created_at" (str): The creation date of the identifier.

    Raises:
        Exception: If an error occurs while retrieving the patient identifiers.
    """
    identifiers = {}
    try:
        status, response = ru.get(
            req, f"patient/{patient_uuid}/identifier", {"v": "full"}
        )
        if status:
            for identifier in response["results"]:
                if (
                    identifier["identifierType"]["uuid"]
                    == Constants.DOTS_IDENTIFIER.value
                ):
                    identifiers["dots"] = {
                        "type": identifier["identifierType"]["uuid"],
                        "identifier": identifier["identifier"],
                        "created_at": identifier["auditInfo"]["dateCreated"],
                        "location": identifier["location"]["uuid"],
                    }
                else:
                    identifiers["mdr"] = {
                        "type": identifier["identifierType"]["uuid"],
                        "identifier": identifier["identifier"],
                        "created_at": identifier["auditInfo"]["dateCreated"],
                    }

        return identifiers
    except Exception as e:
        raise Exception(str(e))


def enroll_patient_in_program(req, patientid, data):
    """
    Enrolls a patient in a program.

    Parameters:
        req (Request): The request object.
        patientid (str): The UUID of the patient.
        data (dict): The data for program enrollment, including the following fields:
            - "program" (str): The UUID of the program to enroll the patient in.
            - "enrollmentdate" (str): The date of enrollment.
            - "facility" (str, optional): The UUID of the facility where the enrollment takes place.
              Defaults to None.
            - "district" (str, optional): The UUID of the district where the enrollment takes place.
              Defaults to None.
            - "completiondate" (str, optional): The date of program completion. Defaults to None.
            - Additional fields representing the workflow UUIDs of the program's workflows,
              along with their corresponding start and end dates. The field names should match the
              workflow UUIDs.

    Returns:
        str: The UUID of the program enrollment.

    Raises:
        Exception: If an error occurs while enrolling the patient in the program.
    """
    try:
        location = data.get("facility")
        if not location:
            location = data.get("district")
        if not location and req.session.get("location_enrolled_in"):
            location = req.session.get("location_enrolled_in")["uuid"]
        program_body = {
            "patient": patientid,
            "program": data["program"],
            "dateEnrolled": data["enrollmentdate"],
            "location": location,
            "dateCompleted": data["completiondate"]
            if not data["completiondate"] == ""
            else None,
            "states": [
                {
                    "state": data.get(work_flow_uuid, None),
                    "startDate": data["enrollmentdate"],
                    "endDate": data["completiondate"]
                    if not data["completiondate"] == ""
                    else None,
                }
                for work_flow_uuid in get_programs(
                    req, uuid=data["program"], params={"v": "custom:(allWorkflows)"}
                )
                if data.get(work_flow_uuid)
            ],
        }
        if "identifier" in data:
            patient_identifier = {
                "identifier": data["identifier"],
                "identifierType": data["identifierType"],
                "location": data.get("facility", data.get("district", None)),
            }

            ru.post(req, f"patient/{patientid}/identifier", patient_identifier)
        status, response = ru.post(req, "programenrollment", program_body)
        if status:
            return response["uuid"]
    except Exception as e:
        logger.error(e, exc_info=True)
        raise Exception(str(e))


def get_program_by_uuid(req, uuid):
    """
    Retrieves a program by its UUID.

    Parameters:
        req (Request): The request object.
        uuid (str): The UUID of the program to retrieve.

    Returns:
        dict: The program information, including the following fields:
            - "uuid" (str): The UUID of the program.
            - "name" (str): The name of the program.
            - "retired" (bool): Indicates if the program is retired.
            - "allWorkflows" (list): A list of workflow UUIDs associated with the program.

    Raises:
        Exception: If an error occurs while retrieving the program.
    """
    try:
        status, response = ru.get(
            req,
            f"program/{uuid}",
            {
                "v": "custom:(uuid,name,retired,allWorkflows)",
                "lang": req.session["locale"],
            },
        )
        if status:
            return response
    except Exception as e:
        raise Exception(e)


def get_programs(req, uuid=None, params=None):
    """
    Retrieves programs or a specific program by UUID.

    Parameters:
        req (Request): The request object.
        uuid (str, optional): The UUID of the specific program to retrieve. Defaults to None.
        params (dict, optional): Additional query parameters. Defaults to None.

    Returns:
        list or dict: If `uuid` is provided, returns a list of workflow UUIDs associated with the program.
                      If `uuid` is not provided, returns a list of programs, each represented as a dictionary
                      with the following fields:
                        - "uuid" (str): The UUID of the program.
                        - "name" (str): The name of the program.
                        - "retired" (bool): Indicates if the program is retired.
                        - "allWorkflows" (list): A list of workflow UUIDs associated with the program.
                      Returns None if no programs are found.

    Raises:
        Exception: If an error occurs while retrieving the program(s).
    """
    if uuid:
        status, response = ru.get(req, f"program/{uuid}", params)
        if status:
            return [workFlowUuid["uuid"] for workFlowUuid in response["allWorkflows"]]
    status, response = ru.get(
        req, "program", {"v": "custom:(uuid,name,retired,allWorkflows)"}
    )
    programs = []
    if status:
        for program in response["results"]:
            if program["retired"] == False:
                programs.append(program)
        return programs
    else:
        return None


def sort_states(workflowstates, programstates):
    """
    Sorts and retrieves the relevant program state.

    Parameters:
        workflowstates (list): A list of workflow states.
        programstates (list): A list of program states.

    Returns:
        dict or None: The relevant program state represented as a dictionary with the following fields:
            - "concept" (dict): The concept information of the state, including "uuid" and "name".
            - "start_date" (str): The start date of the program state.
        If the relevant program state is not found, None is returned.

    """
    if len(workflowstates) > 0:
        for programstate in programstates:
            state = programstate.get("state")
            if state:
                uuid = state.get("uuid")
                if uuid:
                    concept = next(
                        (
                            {
                                "uuid": ws["concept"]["uuid"],
                                "name": ws["concept"]["display"].title(),
                            }
                            for ws in workflowstates
                            if ws["uuid"] == uuid
                        ),
                        None,
                    )
                    if concept:
                        return {
                            "concept": concept,
                            "start_date": programstate.get("startDate"),
                        }


def get_program_states(program=None):
    """
    Retrieves the states of a program.

    Parameters:
        program (dict, optional): The program object containing information about the program and its workflows.
                                  Defaults to None.

    Returns:
        list: A list of program states, where each state is represented as a dictionary with the following fields:
            - "uuid" (str): The UUID of the state.
            - "concept" (str): The display name of the state concept.
            - "answer" (list): A sorted list of states associated with the workflow, based on the program states.

    """
    states = [
        {
            "uuid": workflow["concept"]["uuid"],
            "concept": workflow["concept"]["display"].title(),
            "answer": sort_states(workflow["states"], program["states"]),
        }
        for workflow in program["program"]["allWorkflows"]
        if not workflow["retired"]
    ]
    return states


def get_enrolled_programs_by_patient(req, uuid, enrollment_id=None):
    """
    Retrieves the enrolled programs for a patient.

    Parameters:
        req (object): The request object.
        uuid (str): The UUID of the patient.
        enrollment_id (str, optional): The UUID of the specific program enrollment. Defaults to None.

    Returns:
        dict or list or None: If enrollment_id is provided, returns a dictionary containing the details of the specific program enrollment, including:
            - "uuid" (str): The UUID of the program enrollment.
            - "program" (dict): The program information, including "uuid" and "name".
            - "dateEnrolled" (str): The date of enrollment.
            - "dateCompleted" (str): The date of completion.
            - "location" (dict): The location information, including "uuid" and "name".
            - "outcome" (str): The outcome of the program enrollment.
            - "states" (list): A list of program states.

        If enrollment_id is not provided, returns a list of dictionaries containing the details of all enrolled programs, including the same fields as above.
        If no enrolled programs are found, returns None.

    Raises:
        Exception: If an error occurs while retrieving the enrolled programs.
    """
    representation = (
        "custom:(uuid,program,states,dateEnrolled,dateCompleted,location,outcome)"
    )
    if enrollment_id:
        try:
            status, response = ru.get(
                req,
                f"programenrollment/{enrollment_id}",
                {
                    "v": "custom:(uuid,program,states,dateEnrolled,dateCompleted,location,outcome)",
                    "lang": req.session["locale"],
                },
            )
            if status:
                return {
                    "uuid": response["uuid"],
                    "program": {
                        "uuid": response["program"]["uuid"],
                        "name": response["program"]["name"],
                    },
                    "dateEnrolled": response["dateEnrolled"],
                    "dateCompleted": response["dateCompleted"],
                    "location": {
                        "uuid": response["location"]["uuid"],
                        "name": response["location"]["name"],
                    },
                    "outcome": response["outcome"],
                    "states": get_program_states(program=response),
                }
        except Exception as e:
            logger.error(e, exc_info=True)
            raise Exception(str(e))

    try:
        status, response = ru.get(
            req,
            "programenrollment",
            {"patient": uuid, "v": representation, "lang": req.session["locale"]},
        )
        if status:
            if len(response["results"]) <= 0:
                return None
            programs_info = [
                {
                    "uuid": program["uuid"],
                    "program": {
                        "uuid": program["program"]["uuid"],
                        "name": program["program"]["name"],
                    },
                    "dateEnrolled": program["dateEnrolled"],
                    "dateCompleted": program["dateCompleted"],
                    "location": {
                        "uuid": program["location"]["uuid"],
                        "name": program["location"]["name"],
                    },
                    "outcome": program["outcome"],
                    "states": get_program_states(program=program),
                }
                for program in response["results"]
            ]
            return programs_info
    except Exception as e:
        logger.error(e, exc_info=True)
        raise Exception(e)


def get_patient_dashboard_info(
    req, patientuuid, programuuid, is_mdrtb=None, get_lab_data=True
):
    """
    Retrieves the dashboard information for a patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        programuuid (str): The UUID of the program enrollment.
        isMdrtb (bool, optional): Specifies if the program is for MDR-TB. Defaults to None.

    Returns:
        tuple: A tuple containing the following elements:
            - patient (dict): The patient information.
            - program (dict or None): The program information or None if not found.
            - transfer_out (list): A list of transfer out encounters.
            - forms (dict): A dictionary of different forms based on the program type. The keys represent the form types, and the values are the corresponding encounters.
            - lab_results (list): A list of recent lab test results.

    Raises:
        Exception: If an error occurs while retrieving the dashboard information.
    """
    try:
        patient = get_patient(req, patientuuid)
        program = get_enrolled_programs_by_patient(
            req, patientuuid, enrollment_id=programuuid
        )
        treatment_outcome = get_patient_treatment_outcome(
            req, patientuuid, Concepts.TB_TREATMENT_OUTCOME.value
        )
        transfer_out = fu.get_encounters_by_patient_and_type(
            req, patientuuid, EncounterType.TRANSFER_OUT.value
        )
        lab_results = None
        if get_lab_data:
            lab_results = cu.get_lab_test_orders_for_dashboard(req, patientuuid)
        if is_mdrtb:
            treatment_outcome = get_patient_treatment_outcome(
                req, patientuuid, Concepts.MDR_TB_TREATMENT_OUTCOME.value
            )
            forms = {
                "tb03us": fu.get_encounters_by_patient_and_type(
                    req, patientuuid, EncounterType.TB03u_MDR.value
                ),
                "aes": fu.get_ae_form_with_symptoms(req, patientuuid),
                "regimens": fu.get_encounters_by_patient_and_type(
                    req, patientuuid, EncounterType.PV_REGIMEN.value
                ),
                "drug_resistance_forms": fu.get_encounters_by_patient_and_type(
                    req, patientuuid, EncounterType.RESISTANCE_DURING_TREATMENT.value
                ),
            }
        else:
            forms = {
                "tb03s": fu.get_encounters_by_patient_and_type(
                    req, patientuuid, EncounterType.TB03.value
                ),
                "form89s": fu.get_encounters_by_patient_and_type(
                    req, patientuuid, EncounterType.FROM_89.value
                ),
            }
        return (patient, program, treatment_outcome, transfer_out, forms, lab_results)
    except Exception as e:
        raise Exception(str(e))


def get_enrolled_program_by_uuid(req, programid):
    """
    Retrieves the enrolled program by its UUID.

    Parameters:
        req (object): The request object.
        programid (str): The UUID of the enrolled program.

    Returns:
        dict: The enrolled program information.

    Raises:
        Exception: If an error occurs while retrieving the program.
    """
    try:
        status, response = ru.get(req, f"programenrollment/{programid}", {"v": "full"})
        if status:
            return response
    except Exception as e:
        raise Exception(str(e))


def check_if_patient_enrolled_in_mdrtb(req, patient_uuid):
    """
    Checks if a patient is enrolled in the MDR-TB program.

    Parameters:
        req (object): The request object.
        patient_uuid (str): The UUID of the patient.

    Returns:
        bool: True if the patient is enrolled in the MDR-TB program, False otherwise.

    Raises:
        Exception: If an error occurs while checking the enrollment status.
    """
    try:
        programs = get_enrolled_programs_by_patient(req, patient_uuid)
        for program in programs:
            if program["program"]["uuid"] == Constants.MDRTB_PROGRAM.value:
                return True
        return False
    except Exception as e:
        raise Exception(e)


def get_patient_treatment_outcome(req, patientuuid, concept):
    try:
        status, response = ru.get(
            req,
            "obs",
            {"patient": patientuuid, "concept": concept, "v": "custom:(value)"},
        )
        if status:
            return response["results"][0]["value"]["display"]
    except Exception:
        return None
