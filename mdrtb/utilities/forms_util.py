import utilities.metadata_util as mu
import utilities.restapi_utils as ru
from datetime import datetime
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.encounterType import EncounterType
import utilities.common_utils as cu


def get_form_concepts(concept_ids, req):
    """
    Retrieves concepts and their answers based on the provided concept IDs.

    Parameters:
        concept_ids (list): A list of concept IDs.
        req (object): The request object.

    Returns:
        dict: A dictionary mapping concepts to their answers.

    Raises:
        Exception: If an error occurs while retrieving the concepts.

    """
    concept_dict = {}
    for concept in concept_ids:
        try:
            response = mu.get_concept(req, concept)
            if response:
                answers = []
                for answer in response["answers"]:
                    for name in answer["names"]:
                        if (
                            name["conceptNameType"] == "FULLY_SPECIFIED"
                            and name["locale"] == req.session["locale"]
                        ):
                            answers.append(
                                {"uuid": answer["uuid"], "name": name["display"]}
                            )
                            break

                for name in response["names"]:
                    if name["locale"] == "en":
                        key = name["name"].lower().replace(" ", "").replace("-", "")
                        concept_dict[key] = answers
        except Exception as e:
            continue
    return concept_dict


def get_patient_tb03_forms(req, patientuuid):
    """
    Retrieves the TB03 forms for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.

    Returns:
        list or None: A list of TB03 forms if they exist for the patient, None otherwise.

    """
    status, response = ru.get(req, "mdrtb/tb03", {"v": "full", "q": patientuuid})
    if status:
        return response["results"]
    else:
        return None


def get_tb03_by_uuid(req, uuid):
    """
    Retrieves a specific TB03 form by uuid.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the Form.

    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.

    """

    status, response = ru.get(req, f"mdrtb/tb03/{uuid}", {"v": "full"})
    if status:
        return response
    else:
        return None


def create_update_tb03(req, patientuuid, data, formid=None):
    """
    Creates or updates a TB03 form for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the TB03 form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.

    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.

    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.

    """
    patient_program_uuid = req.session["current_patient_program_flow"][
        "current_program"
    ]["uuid"]
    encounter_type = EncounterType.TB03.value
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    current_location = req.session["current_patient_program_flow"]["current_program"][
        "location"
    ]["uuid"]
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                tb03 = {
                    "patientProgramUuid": patient_program_uuid,
                    "encounter": {"uuid": response["uuid"], "obs": []},
                }
            for obs in response["obs"]:
                if obs["concept"]["uuid"] == Concepts.PATIENT_PROGRAM_ID.value:
                    tb03["encounter"]["obs"].append(
                        {
                            "uuid": obs["uuid"],
                            "person": obs["person"]["uuid"],
                            "obsDatetime": obs["obsDatetime"],
                            "concept": obs["concept"]["uuid"],
                            "value": obs["value"],
                        }
                    )
                for key, value in data.items():
                    if value:
                        if key == obs["concept"]["uuid"]:
                            tb03["encounter"]["obs"].append(
                                {
                                    "uuid": obs["uuid"],
                                    "person": obs["person"]["uuid"],
                                    "obsDatetime": obs["obsDatetime"],
                                    "concept": obs["concept"]["uuid"],
                                    "value": value
                                    if not cu.is_date(value)
                                    else cu.date_to_sql_format(value),
                                }
                            )

        except Exception as e:
            raise Exception(e)
    else:
        tb03 = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {
                "patient": patientuuid,
                "encounterType": encounter_type,
                "encounterDatetime": current_date_time,
                "location": current_location,
                "obs": [
                    # Patient Program Id
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": Concepts.PATIENT_PROGRAM_ID.value,
                    }
                ],
            },
        }
        for key, value in data.items():
            if key == "csrfmiddlewaretoken":
                continue
            if value:
                tb03["encounter"]["obs"].append(
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": key,
                        "value": value
                        if not cu.is_date(value)
                        else cu.date_to_sql_format(value),
                    }
                )
    try:
        url = f"mdrtb/tb03/{formid}" if formid else "mdrtb/tb03"
        # This returns the newly created TB03 form

        status, _ = ru.post(req, url, tb03)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def get_encounters_by_patient_and_type(req, patientid, encounterType, params=None):
    """
    Retrieves encounters for a specific patient and encounter type.

    Parameters:
        req (object): The request object.
        patientid (str): The UUID of the patient.
        encounterType (str): The UUID of the encounter type.

    Returns:
        list: A list of encounters for the patient and encounter type, or None if an error occurs.

    """
    try:
        params = (
            "custom:(uuid,location,encounterDatetime)" if params is None else params
        )
        status, response = ru.get(
            req,
            "encounter",
            {
                "v": params,
                "encounterType": encounterType,
                "patient": patientid,
            },
        )
        if status:
            return response["results"]
    except Exception as e:
        return None


def remove_duplicate_concepts(concept_field, form_field):
    """
    Removes duplicate concepts from a concept field based on a form field.

    Parameters:
        concept_field (list): The list of concepts to remove duplicates from.
        form_field (dict): The form field containing the concept to compare against.

    Returns:
        None

    """
    if form_field:
        for concept in concept_field:
            if form_field["uuid"] == concept["uuid"]:
                concept_field.remove(concept)


def remove_tb03_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a TB03 form data.

    Parameters:
        concepts (dict): The dictionary of concepts.
        form_data (dict): The form data containing the concepts.

    Returns:
        None
    """
    remove_duplicate_concepts(
        concepts.get("treatmentcenterforip", []), form_data.get("treatmentSiteIP", None)
    )
    remove_duplicate_concepts(
        concepts.get("treatmentcenterforcp", []), form_data.get("treatmentSiteCP", None)
    )
    remove_duplicate_concepts(
        concepts.get("causeofdeath", []), form_data.get("causeOfDeath", None)
    )
    remove_duplicate_concepts(
        concepts.get("resistancetype", []), form_data.get("resistanceType", None)
    )
    remove_duplicate_concepts(
        concepts.get("resultofhivtest", []), form_data.get("hivStatus", None)
    )
    remove_duplicate_concepts(
        concepts.get("siteoftbdisease", []), form_data.get("anatomicalSite", None)
    )
    remove_duplicate_concepts(
        concepts.get("tuberculosispatientcategory", []),
        form_data.get("patientCategory", None),
    )
    remove_duplicate_concepts(
        concepts.get("tuberculosistreatmentoutcome", []),
        form_data.get("treatmentOutcome", None),
    )


def create_update_tb03u(req, patientuuid, data, formid=None):
    """
    Creates or updates a TB03u form for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the TB03 form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.

    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.

    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.

    """

    patient_program_uuid = req.session["current_patient_program_flow"][
        "current_program"
    ]["uuid"]
    encounter_type = EncounterType.TB03u_MDR.value
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    patient_default_location = req.session["current_patient_program_flow"][
        "current_program"
    ]["location"]["uuid"]
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                tb03u = {
                    "patientProgramUuid": patient_program_uuid,
                    "encounter": {"uuid": response["uuid"], "obs": []},
                }
            for obs in response["obs"]:
                if obs["concept"]["uuid"] == Concepts.PATIENT_PROGRAM_ID.value:
                    tb03u["encounter"]["obs"].append(
                        {
                            "uuid": obs["uuid"],
                            "person": obs["person"]["uuid"],
                            "obsDatetime": obs["obsDatetime"],
                            "concept": obs["concept"]["uuid"],
                            "value": obs["value"],
                        }
                    )
                for key, value in data.items():
                    if value:
                        if key == obs["concept"]["uuid"]:
                            tb03u["encounter"]["obs"].append(
                                {
                                    "uuid": obs["uuid"],
                                    "person": obs["person"]["uuid"],
                                    "obsDatetime": obs["obsDatetime"],
                                    "concept": obs["concept"]["uuid"],
                                    "value": value
                                    if not cu.is_date(value)
                                    else cu.date_to_sql_format(value),
                                }
                            )
        except Exception as e:
            raise Exception(str(e))
    else:
        tb03u = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {
                "patient": patientuuid,
                "encounterType": encounter_type,
                "encounterDatetime": current_date_time,
                "location": data.get(
                    "facility", data.get("district", patient_default_location)
                ),
                "obs": [
                    # Patient Program Id
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": Concepts.PATIENT_PROGRAM_ID.value,
                    }
                ],
            },
        }
        for key, value in data.items():
            if key == "csrfmiddlewaretoken":
                continue
            if value:
                tb03u["encounter"]["obs"].append(
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": key,
                        "value": value
                        if not cu.is_date(value)
                        else cu.date_to_sql_format(value),
                    }
                )
    try:
        print("============")
        print(tb03u)
        print("============")
        # This returns the newly created TB03 form
        url = f"mdrtb/tb03u/{formid}" if formid else "mdrtb/tb03u"

        status, _ = ru.post(req, url, tb03u)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def get_tb03u_by_uuid(req, uuid):
    """
    Retrieves a specific TB03 form by uuid.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the Form.

    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.

    """

    status, response = ru.get(req, f"mdrtb/tb03u/{uuid}", {"v": "full"})
    if status:
        return response
    else:
        return None


def remove_tb03u_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a TB03 form data.

    Parameters:
        concepts (dict): The dictionary of concepts.
        form_data (dict): The form data containing the concepts.

    Returns:
        None
    """
    remove_duplicate_concepts(
        concepts.get("siteoftbdisease", []), form_data.get("anatomicalSite", None)
    )
    remove_duplicate_concepts(
        concepts.get("mdrtbstatus", []), form_data.get("mdrStatus", None)
    )
    remove_duplicate_concepts(
        concepts.get("prescribedtreatment", []), form_data.get("patientCategory", None)
    )

    remove_duplicate_concepts(
        concepts.get("treatmentlocation", []), form_data.get("treatmentLocation", None)
    )
    remove_duplicate_concepts(
        concepts.get("resistancetype", []), form_data.get("resistanceType", None)
    )
    remove_duplicate_concepts(
        concepts.get("methodofdetection", []), form_data.get("basisForDiagnosis", None)
    )

    remove_duplicate_concepts(
        concepts.get("resultofhivtest", []), form_data.get("hivStatus", None)
    )
    remove_duplicate_concepts(
        concepts.get("multidrugresistanttuberculosistreatmentoutcome", []),
        form_data.get("treatmentOutcome", None),
    )
    remove_duplicate_concepts(
        concepts.get("causeofdeath", []), form_data.get("causeOfDeath", None)
    )


def create_update_adverse_event(req, patientuuid, data, formid=None):
    """
    Creates or updates a Adverse Events form for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the TB03 form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.

    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.

    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.

    """

    patient_program_uuid = req.session["current_patient_program_flow"][
        "current_program"
    ]["uuid"]
    encounter_type = EncounterType.ADVERSE_EVENT.value
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    patient_location = req.session["current_patient_program_flow"]["current_program"][
        "location"
    ]["uuid"]
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                ae = {
                    "patientProgramUuid": patient_program_uuid,
                    "encounter": {"uuid": response["uuid"], "obs": []},
                }
            for obs in response["obs"]:
                if obs["concept"]["uuid"] == Concepts.PATIENT_PROGRAM_ID.value:
                    ae["encounter"]["obs"].append(
                        {
                            "uuid": obs["uuid"],
                            "person": obs["person"]["uuid"],
                            "obsDatetime": obs["obsDatetime"],
                            "concept": obs["concept"]["uuid"],
                            "value": obs["value"],
                        }
                    )
                for key, value in data.items():
                    if value:
                        if key == obs["concept"]["uuid"]:
                            ae["encounter"]["obs"].append(
                                {
                                    "uuid": obs["uuid"],
                                    "person": obs["person"]["uuid"],
                                    "obsDatetime": obs["obsDatetime"],
                                    "concept": obs["concept"]["uuid"],
                                    "value": value
                                    if not cu.is_date(value)
                                    else cu.date_to_sql_format(value),
                                }
                            )
        except Exception as e:
            raise Exception
    else:
        ae = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {
                "patient": patientuuid,
                "encounterType": encounter_type,
                "encounterDatetime": current_date_time
                if not any(data.get("encounterDateTime"))
                else data.get("encounterDateTime"),
                "location": patient_location,
                "obs": [
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": Concepts.PATIENT_PROGRAM_ID.value,
                    }
                ],
            },
        }
        for key, value in data.items():
            if key == "csrfmiddlewaretoken":
                continue
            if key == "encounterDateTime":
                continue
            if value:
                ae["encounter"]["obs"].append(
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": key,
                        "value": value
                        if not cu.is_date(value)
                        else cu.date_to_sql_format(value),
                    }
                )
    try:
        url = f"mdrtb/adverseevents/{formid}" if formid else "mdrtb/adverseevents"
        status, response = ru.post(req, url, ae)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def get_ae_by_uuid(req, uuid):
    """
    Retrieves a specific AE form by uuid.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the Form.

    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.

    """

    status, response = ru.get(req, f"mdrtb/adverseevents/{uuid}", {"v": "full"})
    if status:
        return response
    else:
        return None


def remove_ae_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from an AE form data.

    Parameters:
        concepts (dict): The dictionary of concepts.
        form_data (dict): The form data containing the concepts.

    Returns:
        None
    """

    clone_concepts = concepts.copy()
    remove_duplicate_concepts(
        clone_concepts.get("adverseevent", []), form_data.get("advereEvent", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("adverseeventaction", []), form_data.get("actionTaken", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("adverseeventaction2", []),
        form_data.get("actionTaken2", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("adverseeventaction3", []),
        form_data.get("actionTaken3", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("adverseeventaction5", []),
        form_data.get("actionTaken5", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("actiontakeninresponsetotheevent", []),
        form_data.get("actionTaken4", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("adverseeventoutcome", []),
        form_data.get("actionOutcome", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("adverseeventtype", []), form_data.get("typeOfEvent", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("causalityassessmentresult1", []),
        form_data.get("casualityAssessmentResult", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("causalityassessmentresult2", []),
        form_data.get("casualityAssessmentResult2", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("causalityassessmentresult3", []),
        form_data.get("casualityAssessmentResult3", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("causalitydrug1", []), form_data.get("casualityDrug", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("causalitydrug2", []), form_data.get("casualityDrug2", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("causalitydrug3", []), form_data.get("casualityDrug3", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("drugrechallenge", []),
        form_data.get("drugRechallenge", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("meddracode", []), form_data.get("meddraCode", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("saetype", []), form_data.get("typeOfSAE", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("specialinteresteventtype", []),
        form_data.get("typeOfSpecialEvent", None),
    )
    return clone_concepts


def create_update_form89(req, patientuuid, data, formid=None):
    """
    Creates or updates a Form89 for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the TB03 form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.

    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.

    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.

    """

    patient_program_uuid = req.session["current_patient_program_flow"][
        "current_program"
    ]["uuid"]
    encounter_type = EncounterType.FROM_89.value
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    patient_location = req.session["current_patient_program_flow"]["current_program"][
        "location"
    ]["uuid"]
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                form89 = {
                    "patientProgramUuid": patient_program_uuid,
                    "encounter": {"uuid": response["uuid"], "obs": []},
                }
            for obs in response["obs"]:
                if obs["concept"]["uuid"] == Concepts.PATIENT_PROGRAM_ID.value:
                    form89["encounter"]["obs"].append(
                        {
                            "uuid": obs["uuid"],
                            "person": obs["person"]["uuid"],
                            "obsDatetime": obs["obsDatetime"],
                            "concept": obs["concept"]["uuid"],
                            "value": obs["value"],
                        }
                    )
                for key, value in data.items():
                    if value:
                        if key == obs["concept"]["uuid"]:
                            form89["encounter"]["obs"].append(
                                {
                                    "uuid": obs["uuid"],
                                    "person": obs["person"]["uuid"],
                                    "obsDatetime": obs["obsDatetime"],
                                    "concept": obs["concept"]["uuid"],
                                    "value": value
                                    if not cu.is_date(value)
                                    else cu.date_to_sql_format(value),
                                }
                            )
        except Exception as e:
            raise Exception
    else:
        form89 = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {
                "patient": patientuuid,
                "encounterType": encounter_type,
                "encounterDatetime": current_date_time,
                "location": patient_location,
                "obs": [
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": Concepts.PATIENT_PROGRAM_ID.value,
                    }
                ],
            },
        }
        for key, value in data.items():
            if key == "csrfmiddlewaretoken":
                continue
            if value:
                form89["encounter"]["obs"].append(
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": key,
                        "value": value
                        if not cu.is_date(value)
                        else cu.date_to_sql_format(value),
                    }
                )
    try:
        url = f"mdrtb/form89/{formid}" if formid else "mdrtb/form89"
        status, _ = ru.post(req, url, form89)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def get_form89_by_uuid(req, uuid):
    """
    Retrieves a specific Form89 by uuid.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the Form.

    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.

    """

    try:
        status, response = ru.get(req, f"mdrtb/form89/{uuid}", {"v": "full"})
        if status:
            return response
        else:
            return None
    except Exception as e:
        raise Exception(str(e))


def remove_form89_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a Form89  data.

    Parameters:
        concepts (dict): The dictionary of concepts.
        form_data (dict): The form data containing the concepts.

    Returns:
        None
    """

    clone_concepts = concepts.copy()
    remove_duplicate_concepts(
        clone_concepts.get("circumstancesofdetection", []),
        form_data.get("circumstancesOfDetection", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("cmacplace", []), form_data.get("placeOfCommission", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("locationtype", []), form_data.get("locationType", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("methodofdetection", []),
        form_data.get("methodOfDetection", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("placeofdetection", []),
        form_data.get("placeOfDetection", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("populationcategory", []),
        form_data.get("populationCategory", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("prescribedtreatment", []),
        form_data.get("prescribedTreatment", None),
    )
    remove_duplicate_concepts(
        clone_concepts.get("profession", []), form_data.get("profession", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("siteoftbdisease", []), form_data.get("pulSite", None)
    )
    return clone_concepts


def create_update_regimen_form(req, patientuuid, data, formid=None):
    """
    Creates or updates a Regimen Form for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the TB03 form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.

    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.

    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.

    """

    patient_program_uuid = req.session["current_patient_program_flow"][
        "current_program"
    ]["uuid"]
    encounter_type = EncounterType.PV_REGIMEN.value
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    patient_location = req.session["current_patient_program_flow"]["current_program"][
        "location"
    ]["uuid"]
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                regimen = {
                    "patientProgramUuid": patient_program_uuid,
                    "encounter": {"uuid": response["uuid"], "obs": []},
                }
            for obs in response["obs"]:
                if obs["concept"]["uuid"] == Concepts.PATIENT_PROGRAM_ID.value:
                    regimen["encounter"]["obs"].append(
                        {
                            "uuid": obs["uuid"],
                            "person": obs["person"]["uuid"],
                            "obsDatetime": obs["obsDatetime"],
                            "concept": obs["concept"]["uuid"],
                            "value": obs["value"],
                        }
                    )
                for key, value in data.items():
                    if value:
                        if key == obs["concept"]["uuid"]:
                            regimen["encounter"]["obs"].append(
                                {
                                    "uuid": obs["uuid"],
                                    "person": obs["person"]["uuid"],
                                    "obsDatetime": obs["obsDatetime"],
                                    "concept": obs["concept"]["uuid"],
                                    "value": value
                                    if not cu.is_date(value)
                                    else cu.date_to_sql_format(value),
                                }
                            )
        except Exception as e:
            raise Exception(str(e))
    else:
        regimen = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {
                "patient": patientuuid,
                "encounterType": encounter_type,
                "encounterDatetime": current_date_time
                if not any(data.get("encounterDateTime"))
                else data.get("encounterDateTime"),
                "location": patient_location,
                "obs": [
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": Concepts.PATIENT_PROGRAM_ID.value,
                    }
                ],
            },
        }
        for key, value in data.items():
            if key == "csrfmiddlewaretoken":
                continue
            if key == "encounterDateTime":
                continue
            if value:
                regimen["encounter"]["obs"].append(
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": key,
                        "value": value
                        if not cu.is_date(value)
                        else cu.date_to_sql_format(value),
                    }
                )
    try:
        url = f"mdrtb/regimen/{formid}" if formid else "mdrtb/regimen"
        #
        #
        #
        status, _ = ru.post(req, url, regimen)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def get_regimen_by_uuid(req, uuid):
    """
    Retrieves a specific Regimen form by uuid.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the Form.

    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.

    """

    try:
        status, response = ru.get(req, f"mdrtb/regimen/{uuid}", {"v": "full"})
        if status:
            return response
        else:
            return None
    except Exception as e:
        raise Exception(str(e))


def remove_regimen_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a Regimen form data.

    Parameters:
        concepts (dict): The dictionary of concepts.
        form_data (dict): The form data containing the concepts.

    Returns:
        None
    """

    clone_concepts = concepts.copy()
    remove_duplicate_concepts(
        clone_concepts.get("fundingsource", []), form_data.get("fundingSource", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("resistancetype", []), form_data.get("resistanceType", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("sldregimentype", []), form_data.get("sldRegimen", None)
    )
    remove_duplicate_concepts(
        clone_concepts.get("cmacplace", []), form_data.get("placeOfCommission", None)
    )

    return clone_concepts


def get_drug_resistance_form_by_uuid(req, uuid):
    """
    Retrieves a specific Drug Resistance form by uuid.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the Form.

    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.

    """

    try:
        status, response = ru.get(req, f"mdrtb/drugresistance/{uuid}", {"v": "full"})
        if status:
            return response
        else:
            return None
    except Exception as e:
        raise Exception(str(e))


def create_update_drug_resistence_form(req, patientuuid, data, formid=None):
    """
    Creates or updates a Drug resistance Form for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the TB03 form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.

    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.

    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.

    """

    patient_program_uuid = req.session["current_patient_program_flow"][
        "current_program"
    ]["uuid"]
    encounter_type = EncounterType.RESISTANCE_DURING_TREATMENT.value
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    patient_location = req.session["current_patient_program_flow"]["current_program"][
        "location"
    ]["uuid"]
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                drug_resistance = {
                    "patientProgramUuid": patient_program_uuid,
                    "encounter": {"uuid": response["uuid"], "obs": []},
                }
            for obs in response["obs"]:
                if obs["concept"]["uuid"] == Concepts.PATIENT_PROGRAM_ID.value:
                    drug_resistance["encounter"]["obs"].append(
                        {
                            "uuid": obs["uuid"],
                            "person": obs["person"]["uuid"],
                            "obsDatetime": obs["obsDatetime"],
                            "concept": obs["concept"]["uuid"],
                            "value": obs["value"],
                        }
                    )
                for key, value in data.items():
                    if value:
                        if key == obs["concept"]["uuid"]:
                            drug_resistance["encounter"]["obs"].append(
                                {
                                    "uuid": obs["uuid"],
                                    "person": obs["person"]["uuid"],
                                    "obsDatetime": obs["obsDatetime"],
                                    "concept": obs["concept"]["uuid"],
                                    "value": value
                                    if not cu.is_date(value)
                                    else cu.date_to_sql_format(value),
                                }
                            )
        except Exception as e:
            raise Exception(e)
    else:
        drug_resistance = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {
                "patient": patientuuid,
                "encounterType": encounter_type,
                "encounterDatetime": data.get("encounterDateTime", current_date_time),
                "location": patient_location,
                "obs": [
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": Concepts.PATIENT_PROGRAM_ID.value,
                    }
                ],
            },
        }
        for key, value in data.items():
            if key == "csrfmiddlewaretoken":
                continue
            if key == "encounterDatetime":
                continue
            if value:
                drug_resistance["encounter"]["obs"].append(
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": key,
                        "value": value
                        if not cu.is_date(value)
                        else cu.date_to_sql_format(value),
                    }
                )
    try:
        url = f"mdrtb/drugresistance/{formid}" if formid else "mdrtb/drugresistance"

        status, _ = ru.post(req, url, drug_resistance)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def remove_drug_resistance_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a Regimen form data.

    Parameters:
        concepts (dict): The dictionary of concepts.
        form_data (dict): The form data containing the concepts.

    Returns:
        None
    """

    clone_concepts = concepts.copy()
    remove_duplicate_concepts(
        clone_concepts.get("drugresistanceduringtreatment", []),
        form_data.get("drugResistance", None),
    )
    return clone_concepts


def get_transfer_out_by_uuid(req, uuid):
    """
    Retrieves a specific Transfer out form by uuid.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the Form.

    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.

    """

    try:
        status, response = ru.get(req, f"mdrtb/transferout/{uuid}", {"v": "full"})
        if status:
            return response
        else:
            return None
    except Exception as e:
        raise Exception(str(e))


def create_update_tranfer_out_form(req, patientuuid, data, formid=None):
    """
    Creates or updates a Transfer out Form for a specific patient.

    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the TB03 form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.

    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.

    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.

    """

    patient_program_uuid = req.session["current_patient_program_flow"][
        "current_program"
    ]["uuid"]
    encounter_type = EncounterType.TRANSFER_OUT.value
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    patient_location = req.session["current_patient_program_flow"]["current_program"][
        "location"
    ]["uuid"]
    if formid:
        try:
            response = mu.get_encounter_by_uuid(req, formid)
            if response:
                transfer_out = {
                    "patientProgramUuid": patient_program_uuid,
                    "encounter": {
                        "uuid": response["uuid"],
                        "encounterDatetime": data.get(
                            "encounterDatetime", response["encounterDatetime"]
                        ),
                        "location": data.get(
                            "facility",
                            data.get("district", response["location"]),
                        ),
                        "obs": [
                            {
                                "person": patientuuid,
                                "obsDatetime": current_date_time_iso,
                                "concept": Concepts.PATIENT_PROGRAM_ID.value,
                            }
                        ],
                    },
                }

        except Exception as e:
            raise Exception(e)
    else:
        transfer_out = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {
                "patient": patientuuid,
                "encounterType": encounter_type,
                "encounterDatetime": data.get("encounterDatetime", current_date_time),
                "location": data.get(
                    "facility",
                    data.get("district", patient_location),
                ),
                "obs": [
                    {
                        "person": patientuuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": Concepts.PATIENT_PROGRAM_ID.value,
                    }
                ],
            },
        }
    try:
        url = f"mdrtb/transferout/{formid}" if formid else "mdrtb/transferout"
        status, _ = ru.post(req, url, transfer_out)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def get_patient_site_of_TB(req, patientuuid):
    """
    Retrieves the site of TB for a patient.

    Parameters:
        req: The request object.
        patientuuid (str): The UUID of the patient.

    Returns:
        dict: A dictionary containing the UUID and name of the site of TB.
    """
    try:
        status, response = ru.get(
            req,
            "encounter",
            {
                "patient": patientuuid,
                "encounterType": EncounterType.TB03.value,
                "v": "custom:(obs)",
            },
        )
        site_of_tb = {}
        if response and len(response["results"]) > 0:
            for ob in response["results"][0]["obs"]:
                if ob["concept"]["uuid"] == Concepts.ANATOMICAL_SITE_OF_TB.value:
                    site_of_tb["uuid"] = ob["value"]["uuid"]
                    site_of_tb["name"] = ob["value"]["display"]
        return site_of_tb
    except Exception as e:
        raise Exception(e)


def get_ae_form_with_symptoms(req, patientuuid):
    try:
        ae_forms = get_encounters_by_patient_and_type(
            req,
            patientuuid,
            EncounterType.ADVERSE_EVENT.value,
            params="custom:(uuid,location,encounterDatetime,obs)",
        )
        if ae_forms:
            ae_forms_with_symptoms = []
            for ae_form in ae_forms:
                for ob in ae_form["obs"]:
                    if ob["concept"]["uuid"] == Concepts.ADVERSE_EVENT.value:
                        symptom = ob["value"]["display"]
                        ae_forms_with_symptoms.append(
                            {
                                "form": {
                                    "uuid": ae_form["uuid"],
                                    "encounterDatetime": ae_form["encounterDatetime"],
                                    "location": ae_form["location"]["name"],
                                },
                                "symptom": symptom,
                            }
                        )
            return ae_forms_with_symptoms
    except Exception as e:
        raise Exception(e)
