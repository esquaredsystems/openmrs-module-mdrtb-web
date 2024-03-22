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
                # Sort answers by name
                answers.sort(key=lambda x: x["name"])
                for name in response["names"]:
                    if name["locale"] == "en":
                        key = name["name"].lower().replace(" ", "").replace("-", "")
                        concept_dict[key] = answers
        except Exception:
            continue
    return concept_dict


def update_existing_form(req, data, form_uuid, patient_uuid):
    try:
        patient_program_uuid = req.session["current_patient_program_flow"]["current_program"]["uuid"]
        current_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        response = mu.get_encounter_by_uuid(req, form_uuid)
        form = {
            "patientProgramUuid": patient_program_uuid,
            "encounter": {"uuid": response["uuid"], "obs": []},
        }
        program_obs = get_obs_from_encounter(response["obs"], Concepts.PATIENT_PROGRAM_ID.value)
        form["encounter"]["obs"].append(
            {
                "uuid": program_obs["uuid"],
                "person": program_obs["person"]["uuid"],
                "obsDatetime": program_obs["obsDatetime"],
                "concept": program_obs["concept"]["uuid"],
                "value": program_obs["value"],
            }
        )
        for key, value in data.items():
            if cu.is_uuid(key) and value:
                existing = get_obs_from_encounter(response["obs"], key)
                if existing:
                    obs = {
                        "uuid": existing["uuid"],
                        "person": existing["person"]["uuid"],
                        "obsDatetime": existing["obsDatetime"],
                        "concept": existing["concept"]["uuid"],
                        "value": value if cu.is_uuid(value)
                        else (cu.date_to_sql_datetime(value) if cu.is_date(value) else value)
                    }
                else:
                    obs = {
                        "person": patient_uuid,
                        "obsDatetime": current_date_time_iso,
                        "concept": key,
                        "value": value if not cu.is_date(value)
                        else (cu.date_to_sql_datetime(value) if cu.is_date(value) else value)
                    }
                form["encounter"]["obs"].append(obs)
    except Exception as e:
        raise Exception(e)
    return form


def create_new_form(req, data, encounter_type, patient_uuid, keys_to_ignore):
    patient_program_uuid = req.session["current_patient_program_flow"]["current_program"]["uuid"]
    form_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    form_date_time_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    current_location = req.session["current_patient_program_flow"]["current_program"]["location"]["uuid"]
    # Overwrite encounter datetime if it was already supplied in data
    try:
        if data.get("encounterDateTime"):
            form_date_time = cu.date_to_sql_datetime(data.get("encounterDateTime"))
            form_date_time_iso = form_date_time
    finally:
        pass
    form = {
        "patientProgramUuid": patient_program_uuid,
        "encounter": {
            "patient": patient_uuid,
            "encounterType": encounter_type,
            "encounterDatetime": form_date_time,
            "location": current_location,
            "obs": [
                # Patient Program Id
                {
                    "person": patient_uuid,
                    "obsDatetime": form_date_time_iso,
                    "concept": Concepts.PATIENT_PROGRAM_ID.value,
                }
            ],
        },
    }
    for key, value in data.items():
        if key in keys_to_ignore:
            continue
        if value:
            form["encounter"]["obs"].append(
                {
                    "person": patient_uuid,
                    "obsDatetime": form_date_time_iso,
                    "concept": key,
                    "value": value
                    if not cu.is_date(value)
                    else cu.date_to_sql_datetime(value),
                }
            )
    return form


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
    except Exception:
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


def get_patient_tb03_forms(req, patient_uuid):
    """
    Retrieves the TB03 forms for a specific patient.
    Parameters:
        req (object): The request object.
        patient_uuid (str): The UUID of the patient.
    Returns:
        list or None: A list of TB03 forms if they exist for the patient, None otherwise.
    """
    status, response = ru.get(req, "mdrtb/tb03", {"v": "full", "q": patient_uuid})
    if status:
        return response["results"]
    else:
        return None


def get_tb03_by_uuid(req, patient_uuid):
    """
    Retrieves a specific TB03 form by patient uuid.
    Parameters:
        req (object): The request object.
        patient_uuid (str): The UUID of the Form.
    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.
    """
    status, response = ru.get(req, f"mdrtb/tb03/{patient_uuid}", {"v": "full"})
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
    try:
        if formid:
            tb03 = update_existing_form(req, data, formid, patientuuid)
            url = f"mdrtb/tb03/{formid}"
            status, _ = ru.post(req, url, tb03)
        else:
            keys_to_ignore = ['csrfmiddlewaretoken']
            tb03 = create_new_form(req, data, EncounterType.TB03.value, patientuuid, keys_to_ignore)
            url = "mdrtb/tb03"
            status, _ = ru.post(req, url, tb03)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def remove_tb03_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a TB03 form data.
    Parameters:
        concepts (dict): The dictionary of concepts.
        form_data (dict): The form data containing the concepts.
    Returns:
        None
    """
    clone_concepts = concepts.copy()
    concept_form_mapping = {
        "treatmentcenterforip": "treatmentSiteIP",
        "treatmentcenterforcp": "treatmentSiteCP",
        "causeofdeath": "causeOfDeath",
        "resistancetype": "resistanceType",
        "resultofhivtest": "hivStatus",
        "anatomicalSite": "anatomicalSite",
        "tuberculosispatientcategory": "patientCategory",
        "tuberculosistreatmentoutcome": "treatmentOutcome",
    }
    for concept_key, form_data_key in concept_form_mapping.items():
        remove_duplicate_concepts(clone_concepts.get(concept_key, []), form_data.get(form_data_key, None))
    return clone_concepts


def get_tb03u_by_uuid(req, uuid):
    """
    Retrieves a specific TB03 form by uuid.
    Parameters:
        req (object): The request object.
        uuid (str): The UUID of the Form.
    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.
    """
    status, response = ru.get(req, f"mdrtb/tb03u/{uuid}", {"v": "full"})
    if status:
        return response
    else:
        return None


def create_update_tb03u(req, patientuuid, data, formid=None):
    """
    Creates or updates a TB03u form for a specific patient.
    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.
    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.
    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.
    """
    try:
        if formid:
            tb03u = update_existing_form(req, data, formid, patientuuid)
            url = f"mdrtb/tb03u/{formid}"
            status, _ = ru.post(req, url, tb03u)
        else:
            keys_to_ignore = ["csrfmiddlewaretoken", "country", "region", "district", "facility"]
            tb03u = create_new_form(req, data, EncounterType.TB03u_MDR.value, patientuuid, keys_to_ignore)
            # Set the location to be the district
            current_location = tb03u["encounter"]["location"]
            tb03u["encounter"]["location"] = data.get("facility", data.get("district", current_location))
            url = "mdrtb/tb03u"
            status, _ = ru.post(req, url, tb03u)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def remove_tb03u_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a TB03u form data.
    """
    clone_concepts = concepts.copy()
    concept_form_mapping = {
        "anatomicalsite": "anatomicalSite",
        "mdrtbstatus": "mdrStatus",
        "prescribedtreatment": "patientCategory",
        "treatmentlocation": "treatmentLocation",
        "resistancetype": "resistanceType",
        "methodofdetection": "basisForDiagnosis",
        "resultofhivtest": "hivStatus",
        "multidrugresistanttuberculosistreatmentoutcome": "treatmentOutcome",
        "causeofdeath": "causeOfDeath",
    }
    for concept_key, form_data_key in concept_form_mapping.items():
        remove_duplicate_concepts(clone_concepts.get(concept_key, []), form_data.get(form_data_key, None))
    return clone_concepts


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


def create_update_adverse_event(req, patientuuid, data, formid=None):
    """
    Creates or updates a Adverse Events form for a specific patient.
    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.
    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.
    Raises:
        Exception: If an error occurs while creating or updating the form.
    """
    try:
        if formid:
            ae = update_existing_form(req, data, formid, patientuuid)
            url = f"mdrtb/adverseevents/{formid}"
            status, _ = ru.post(req, url, ae)
        else:
            keys_to_ignore = ['csrfmiddlewaretoken']
            ae = create_new_form(req, data, EncounterType.ADVERSE_EVENT.value, patientuuid, keys_to_ignore)
            url = "mdrtb/adverseevents"
            status, _ = ru.post(req, url, ae)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def remove_ae_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a TB03u form data.
    """
    clone_concepts = concepts.copy()
    concept_form_mapping = {
        "adverseevent": "advereEvent",
        "adverseeventaction": "actionTaken",
        "adverseeventaction2": "actionTaken2",
        "adverseeventaction3": "actionTaken3",
        "actiontakeninresponsetotheevent": "actionTaken4",
        "adverseeventaction5": "actionTaken5",
        "adverseeventoutcome": "actionOutcome",
        "adverseeventtype": "typeOfEvent",
        "causalityassessmentresult1": "casualityAssessmentResult",
        "causalityassessmentresult2": "casualityAssessmentResult2",
        "causalityassessmentresult3": "casualityAssessmentResult3",
        "causalitydrug1": "casualityDrug",
        "causalitydrug2": "casualityDrug2",
        "causalitydrug3": "casualityDrug3",
        "drugrechallenge": "drugRechallenge",
        "saetype": "typeOfSAE",
        "specialinteresteventtype": "typeOfSpecialEvent",
    }
    for concept_key, form_data_key in concept_form_mapping.items():
        remove_duplicate_concepts(clone_concepts.get(concept_key, []), form_data.get(form_data_key, None))
    return clone_concepts


def get_form89_by_uuid(req, uuid):
    """
    Retrieves a specific Form89 by uuid.
    Parameters:
        req (object): The request object.
        uuid (str): The UUID of the Form.
    Returns:
        dict or None: A dict of TB03 form if exists , None otherwise.
    """
    try:
        status, response = ru.get(req, f"mdrtb/form89/{uuid}", {})
        if status:
            return response
        else:
            return None
    except Exception as e:
        raise Exception(str(e))


def create_update_form89(req, patientuuid, data, formid=None):
    """
    Creates or updates a Form89 for a specific patient.
    Parameters:
        req (object): The request object.
        patientuuid (str): The UUID of the patient.
        data (dict): The data for the form.
        formid (str, optional): The UUID of the form to be updated. Defaults to None.
    Returns:
        bool: True if the TB03 form is successfully created or updated, False otherwise.
    Raises:
        Exception: If an error occurs while creating or updating the TB03 form.
    """
    try:
        if formid:
            form89 = update_existing_form(req, data, formid, patientuuid)
            url = f"mdrtb/form89/{formid}"
            status, _ = ru.post(req, url, form89)
        else:
            keys_to_ignore = ["csrfmiddlewaretoken"]
            form89 = create_new_form(req, data, EncounterType.FROM_89.value, patientuuid, keys_to_ignore)
            url = "mdrtb/form89"
            status, _ = ru.post(req, url, form89)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def remove_form89_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a Form89 form data.
    """
    clone_concepts = concepts.copy()
    concept_form_mapping = {
        "circumstancesofdetection": "circumstancesOfDetection",
        "cmacplace": "placeOfCommission",
        "locationtype": "locationType",
        "methodofdetection": "methodOfDetection",
        "placeofdetection": "placeOfDetection",
        "populationcategory": "populationCategory",
        "prescribedtreatment": "prescribedTreatment",
        "profession": "profession",
        "anatomicalsite": "anatomicalSite",
    }
    for concept_key, form_data_key in concept_form_mapping.items():
        remove_duplicate_concepts(clone_concepts.get(concept_key, []), form_data.get(form_data_key, None))
    return clone_concepts


def get_regimen_by_uuid(req, uuid):
    """
    Retrieves a specific Regimen form by uuid.
    Parameters:
        req (object): The request object.
        uuid (str): The UUID of the Form.
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
    try:
        if formid:
            regimen = update_existing_form(req, data, formid, patientuuid)
            url = f"mdrtb/regimen/{formid}"
            status, _ = ru.post(req, url, regimen)
        else:
            keys_to_ignore = ["csrfmiddlewaretoken", "encounterDatetime"]
            # Remove keys with empty values
            data = {key: value for key, value in data.items() if value != ''}
            regimen = create_new_form(req, data, EncounterType.PV_REGIMEN.value, patientuuid, keys_to_ignore)
            url = "mdrtb/regimen"
            status, _ = ru.post(req, url, regimen)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def remove_regimen_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a Regimen form data.
    """
    clone_concepts = concepts.copy()
    concept_form_mapping = {
        "fundingsource": "fundingSource",
        "resistancetype": "resistanceType",
        "sldregimentype": "sldRegimen",
        "cmacplace": "placeOfCommission",
    }
    for concept_key, form_data_key in concept_form_mapping.items():
        remove_duplicate_concepts(clone_concepts.get(concept_key, []), form_data.get(form_data_key, None))
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
    try:
        if formid:
            drugresistance = update_existing_form(req, data, formid, patientuuid)
            url = f"mdrtb/drugresistance/{formid}"
            status, _ = ru.post(req, url, drugresistance)
        else:
            keys_to_ignore = ["csrfmiddlewaretoken", "encounterDatetime"]
            drugresistance = create_new_form(req, data, EncounterType.RESISTANCE_DURING_TREATMENT.value, patientuuid, keys_to_ignore)
            url = "mdrtb/drugresistance"
            status, _ = ru.post(req, url, drugresistance)
        if status:
            return True
    except Exception as e:
        raise Exception(str(e))


def remove_drug_resistance_duplicates(concepts, form_data):
    """
    Removes duplicate concepts from a Drug Resistance form data.
    """
    clone_concepts = concepts.copy()
    concept_form_mapping = {
        "drugresistanceduringtreatment": "drugResistance",
    }
    for concept_key, form_data_key in concept_form_mapping.items():
        remove_duplicate_concepts(clone_concepts.get(concept_key, []), form_data.get(form_data_key, None))
    return clone_concepts


def get_transfer_out_by_uuid(req, uuid):
    """
    Retrieves a specific Transfer out form by uuid.
    Parameters:
        req (object): The request object.
        uuid (str): The UUID of the Form.
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


def get_obs_from_encounter(obs_set, concept_uuid):
    for obs in obs_set:
        if concept_uuid == obs["concept"]["uuid"]:
            return obs
    return None
