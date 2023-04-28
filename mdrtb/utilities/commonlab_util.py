import requests
from django.http import JsonResponse
from . import restapi_utils as ru
from . import common_utils as u
import utilities.metadata_util as mu


def get_commonlab_concepts_by_type(req, type):
    concept_uuid = mu.get_global_properties(req, type)
    status, response = ru.get(
        req, "commonlab/concept", {"type": type, "lang": req.session["locale"]}
    )
    concepts = []
    if status:
        for concept in response["answers"]:
            concepts.append({"name": concept["name"], "uuid": concept["uuid"]})

    return concepts


def get_commonlab_test_groups():
    testGroups = [
        "SEROLOGY",
        "CARDIOLOGY",
        "OPHTHALMOLOGY",
        "BACTERIOLOGY",
        "BIOCHEMISTRY",
        "BLOOD_BANK",
        "CYTOLOGY",
        "HEMATOLOGY",
        "IMMUNOLOGY",
        "MICROBIOLOGY",
        "RADIOLOGY",
        "SONOLOGY",
        "URINALYSIS",
        "OTHER",
    ]
    return testGroups


def get_preffered_handler():
    attributesPrefferedHandler = [
        {
            "value": "org.openmrs.web.attribute.handler.DateFieldGenDatatypeHandler",
            "name": "DateFieldGenDatatype",
        },
        {
            "value": "org.openmrs.web.attribute.handler.LongFreeTextFileUploadHandler",
            "name": "LongFreeTextFileUpload",
        },
        {
            "value": "org.openmrs.web.attribute.handler.BooleanFieldGenDatatypeHandler",
            "name": "BooleanFieldGenDatatype",
        },
        {
            "value": "org.openmrs.web.attribute.handler.LongFreeTextTextareaHandler",
            "name": "LongFreeTextTextarea",
        },
    ]
    return attributesPrefferedHandler


def get_attributes_data_types():
    attributesDataTypes = [
        {
            "value": "org.openmrs.customdatatype.datatype.DateDatatype.name",
            "name": "Date",
            "inputType": "date",
        },
        {
            "value": "org.openmrs.customdatatype.datatype.BooleanDatatype.name",
            "name": "Boolean",
            "inputType": "checkbox",
        },
        {
            "value": "org.openmrs.customdatatype.datatype.LongFreeTextDatatype.name",
            "name": "LongFreeText",
            "inputType": "textarea",
        },
        {
            "value": "org.openmrs.customdatatype.datatype.FreeTextDatatype.name",
            "name": "FreeText",
            "inputType": "text",
        },
        {
            "value": "org.openmrs.customdatatype.datatype.RegexValidatedTextDatatype.name",
            "name": "RegexValidatedText",
            "inputType": "text",
        },
        {
            "value": "org.openmrs.customdatatype.datatype.ConceptDatatype.name",
            "name": "Concept",
            "inputType": "text",
        },
    ]
    return attributesDataTypes


def get_test_types_by_search(req, query):
    status, response = ru.get(req, "commonlab/labtesttype")
    labtests = []
    if status:
        for labtest in response["results"]:
            if (
                labtest["name"].startswith(query)
                or labtest["name"] == query
                or labtest["name"].__contains__(query)
            ):
                labtests.append(labtest)
    return labtests


def get_attributes_of_labtest(req, uuid):
    status, data = ru.get(
        req, "commonlab/labtestattributetype", {"testTypeUuid": uuid, "v": "full"}
    )
    if status:
        sortedAttr = sorted(data["results"], key=lambda x: x["sortWeight"])
        return sortedAttr
    else:
        raise Exception(data["error"]["message"])


def add_edit_test_type(req, data, url):
    status, response = ru.post(req, url, data)
    if status:
        return status, response
    return status, response


def custom_attribute(data, removeDT, removeHandler):
    attribute = {
        "uuid": data["uuid"],
        "name": data["name"],
        "description": data["description"],
        "multisetName": "None" if "multisetName" not in data else data["multisetName"],
        "groupName": "None" if "groupName" not in data else data["groupName"],
        "maxOccurs": data["maxOccurs"],
        "minOccurs": 0 if "minOccurs" not in data else data["minOccurs"],
        "sortWeight": data["sortWeight"],
        "datatypeClassname": {
            "name": u.remove_given_str_from_obj_arr(
                get_attributes_data_types(), removeDT, "commonlab"
            ),
            "value": data["datatypeClassname"],
        },
        "datatypeConfig": ""
        if data["datatypeConfig"] == None
        else data["datatypeConfig"],
        "preferredHandlerClassname": {
            "name": u.remove_given_str_from_obj_arr(
                get_preffered_handler(), removeHandler, "commonlab"
            ),
            "value": data["preferredHandlerClassname"],
        },
        "handlerConfig": "" if data["handlerConfig"] == None else data["handlerConfig"],
    }
    return attribute


def get_patient_encounters(req, uuid):
    status, response = ru.get(req, "encounter", {"patient": uuid})
    if status:
        return response
    else:
        return None


def get_test_groups_and_tests(req):
    status, response = ru.get(req, "commonlab/labtesttype", {})
    if status:
        test_groups = [test["testGroup"] for test in response["results"]]
        lab_tests = response["results"]
    return lab_tests, test_groups


def get_sample_units(req):
    uuid = "5f21ab43-ec32-44b2-88e5-bc4ed2b93fba"
    status, response = ru.get(req, f"concept/{uuid}", {"v": "custom:(setMembers)"})
    units = []
    if status:
        for unit in response["setMembers"]:
            units.append(
                {
                    "uuid": unit["uuid"],
                    "name": unit["display"],
                }
            )
    return units


def get_commonlab_labtesttype(req, uuid):
    status, response = ru.get(req, f"commonlab/labtesttype/{uuid}", {"v": "full"})
    if status:
        return response
    else:
        return None


def get_reference_concept_of_labtesttype(req, labtestid):
    try:
        labtest = get_commonlab_labtesttype(req, labtestid)
        return labtest["referenceConcept"]["uuid"]
    except Exception as e:
        return None


def get_custome_lab_order(full_order):
    order = full_order["order"]
    return {
        "laborder_id": full_order["uuid"],
        "labref": full_order["labReferenceNumber"],
        "order": {
            "patient": order["patient"]["uuid"],
            "encounter": {
                "uuid": order["encounter"]["uuid"],
                "name": order["encounter"]["display"],
            },
            "instructions": ""
            if order["instructions"] == None
            else order["instructions"],
        },
        "labtesttype": {
            "uuid": full_order["labTestType"]["uuid"],
            "name": full_order["labTestType"]["name"],
            "testGroup": full_order["labTestType"]["testGroup"],
        },
    }


def get_custom_attribute_for_labresults(req, orderid):
    context = {"title": "Add Test Results"}
    datatypes = get_attributes_data_types()
    try:
        status, response = ru.get(
            req, f"commonlab/labtestorder/{orderid}", {"v": "custom:(labTestType)"}
        )
        attributes = get_attributes_of_labtest(req, response["labTestType"]["uuid"])
        attrs = []
        for attribute in attributes:
            for datatype in datatypes:
                if datatype["value"].replace(".name", "") == attribute[
                    "datatypeClassname"
                ].replace(".name", ""):
                    attrs.append(
                        {
                            "uuid": attribute["uuid"],
                            "name": attribute["name"],
                            "datatype": attribute["datatypeClassname"],
                            "inputType": datatype["inputType"],
                            "group": attribute["groupName"],
                        }
                    )

        return attrs, response["labTestType"]["uuid"]
    except Exception as e:
        raise Exception(e)
