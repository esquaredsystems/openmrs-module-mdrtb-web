import requests
from django.core.cache import cache
from django.http import JsonResponse
from . import restapi_utils as ru
from . import common_utils as u
import logging
import utilities.metadata_util as mu
import utilities.common_utils as utils
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.constants import Constants
import zlib
import pickle

logger = logging.getLogger("django")


def get_commonlab_concepts_by_type(req, type):
    """
    Retrieves common lab concepts of a specific type.
    Parameters:
        req (object): The request object.
        type (str): The type of common lab concepts to retrieve.
    Returns:
        list: A list of dictionaries representing the common lab concepts. Each dictionary contains the 'name' and 'uuid' of a concept.
    Raises:
        Exception: If an error occurs while retrieving the common lab concepts.
    """
    concept = mu.get_concept(req, mu.get_global_properties(req, type))
    concepts = []
    if concept:
        for answer in concept["answers"]:
            concepts.append({"name": answer["display"], "uuid": answer["uuid"]})

    # Sort concepts by name
    sorted_concepts = sorted(concepts, key=lambda x: x["name"])
    return sorted_concepts


def get_commonlab_test_groups():
    """
    Returns a list of test groups for the Test Types.
    """
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
    """
    Returns a list of dictionaries representing the preferred attribute handlers. Each dictionary contains the 'value' and 'name' of a handler.
    """
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
    """
    Returns a list of dictionaries representing the attribute data types. Each dictionary contains the 'value', 'name', and 'inputType' of a data type.
    """
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
            "inputType": "select",
        },
        {
            "value": "org.openmrs.customdatatype.datatype.FloatDatatype",
            "name": "Float",
            "inputType": "number",
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


def add_edit_test_type(req, data, url):
    """
    Adds or edits a test type using the provided data and URL.

    Parameters:
        req: The request object.
        data (dict): The data containing information about the test type.
        url (str): The URL endpoint for adding or editing the test type.

    Returns:
        tuple: A tuple containing the status (True if successful, False otherwise) and the response data.
    """
    status, response = ru.post(req, url, data)
    if status:
        return status, response
    return status, response


def get_custom_attribute(data, removeDT, removeHandler):
    """
    Creates a custom attribute dictionary based on the provided data.
    Parameters:
        data (dict): The data containing information about the attribute.
        removeDT (str): The string to be removed from the attribute data types.
        removeHandler (str): The string to be removed from the preferred handler class names.
    Returns:
        dict: The custom attribute dictionary.
    """
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


def get_test_groups_and_tests(req):
    """
    Retrieves the lab test type and corresponding test groups.
    Parameters:
        req (object): The request object for making API calls.
    Returns:
        tuple: A tuple containing two lists. The first list contains the lab tests, and the second list contains the test groups.
    """
    status, response = ru.get(req, "commonlab/labtesttype", {"v": "full"})
    if status:
        test_groups = [test["testGroup"] for test in response["results"]]
        lab_tests = response["results"]
    return lab_tests, test_groups


def get_sample_units(req):
    """
    Retrieves the sample units.
    Parameters:
        req (object): The request object for making API calls.
    Returns:
        list: A list of sample units, where each unit is represented as a dictionary with 'uuid' and 'name' keys.
    """
    uuid = Concepts.DOSING_UNIT.value
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
    """
    Retrieves the details of a lab test type by its UUID.
    Parameters:
        req (object): The request object for making API calls.
        uuid (str): The UUID of the lab test type.
    Returns:
        dict: A dictionary containing the details of the lab test type, or None if the retrieval fails.
    """
    status, response = ru.get(req, f"commonlab/labtesttype/{uuid}", {"v": "full"})
    if status:
        return response
    else:
        return None


def get_reference_concept_of_labtesttype(req, labtestid):
    """
    Retrieves the UUID of the reference concept associated with a lab test type.
    Parameters:
        req (object): The request object for making API calls.
        labtestid (str): The UUID of the lab test type.
    Returns:
        str: The UUID of the reference concept, or None if the retrieval fails.
    """
    try:
        labtest = get_commonlab_labtesttype(req, labtestid)
        return labtest["referenceConcept"]["uuid"]
    except Exception:
        return None


def get_custom_lab_order(full_order):
    """
    Extracts and returns a custom representation of a lab order.
    Parameters:
        full_order (dict): The full lab order object.
    Returns:
        dict: A custom representation of the lab order, containing selected information.
    """
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
            "instructions": "" if order["instructions"] is None else order["instructions"],
        },
        "labtesttype": {
            "uuid": full_order["labTestType"]["uuid"],
            "name": full_order["labTestType"]["name"],
            "testGroup": full_order["labTestType"]["testGroup"],
        },
        "careSetting": {
            "uuid": full_order["order"]["careSetting"]["uuid"],
            "name": full_order["order"]["careSetting"]["display"],
        },
    }


def get_attributes_of_labtest(req, lab_test_type):
    """
    Retrieves the attributes of a lab test based on the provided UUID.
    Parameters:
        req: The request object.
        lab_test_type (str): The lab test type.
    Returns:
        list: A list of dictionaries representing the attributes of the lab test. Each dictionary contains detailed information about an attribute.
    Raises:
        Exception: If there is an error retrieving the attributes.
    """
    compressed_attribute_types = cache.get(
        f"{lab_test_type['name'].replace(' ', '')}_attribute_types"
    )
    if compressed_attribute_types:
        return pickle.loads(zlib.decompress(compressed_attribute_types))
    status, data = ru.get(
        req,
        "commonlab/labtestattributetype",
        {"testTypeUuid": lab_test_type["uuid"], "v": "full"},
    )
    if status:
        attribute_types = sorted(data["results"], key=lambda x: x["sortWeight"])
        compressed_attribute_types = zlib.compress(pickle.dumps(attribute_types))
        cache.set(
            f"{lab_test_type['name'].replace(' ', '')}_attribute_types",
            compressed_attribute_types,
            timeout=None,
        )
        return attribute_types
    else:
        raise Exception(data["error"]["message"])


def get_custom_attribute_for_labresults(
        req, orderid, attributes_to_get=None, lab_test_type=None
):
    """
    Retrieves custom attributes for lab results and returns them along with the lab test type UUID.
    Parameters:
        req (object): The request object.
        orderid (str): The UUID of the lab test order.
    Returns:
        tuple: A tuple containing the list of custom attributes for lab results and the lab test type UUID.
    Raises:
        Exception: If an error occurs while retrieving the custom attributes.
    """
    try:
        if attributes_to_get and len(attributes_to_get) <= 0:
            return []
        if lab_test_type is None:
            status, response = ru.get(
                req, f"commonlab/labtestorder/{orderid}", {"v": "custom:(labTestType)"}
            )
            lab_test_type = response["labTestType"]
            lab_test_type_name = response["labTestType"]["name"].replace(" ", "")
        else:
            lab_test_type_name = lab_test_type["name"].replace(" ", "")
        custom_attributes_object = cache.get(
            f"{lab_test_type_name}_custom_attribute_types"
        )
        if custom_attributes_object:
            return pickle.loads(zlib.decompress(custom_attributes_object))
        compressed_attribute_types = cache.get(f"{lab_test_type_name}_attribute_types")
        if compressed_attribute_types:
            attributes = pickle.loads(zlib.decompress(compressed_attribute_types))
        else:
            attributes = get_attributes_of_labtest(req, lab_test_type)
        attrs = []
        datatypes = get_attributes_data_types()
        for attribute in attributes:
            if attributes_to_get:
                if attribute["uuid"] in attributes_to_get:
                    for datatype in datatypes:
                        if datatype["value"].replace(".name", "") == attribute[
                            "datatypeClassname"
                        ].replace(".name", ""):
                            if datatype["inputType"] == "select":
                                try:
                                    concept = mu.get_concept(
                                        req, attribute["datatypeConfig"]
                                    )
                                    concept_full_name = concept["display"]
                                    if (
                                            concept["name"]["conceptNameType"]
                                            != Constants.FULLY_SPECIFIED.value
                                    ):
                                        for name in concept["names"]:
                                            if (
                                                    name["conceptNameType"]
                                                    == Constants.FULLY_SPECIFIED.value
                                                    and name["locale"]
                                                    == req.session["locale"]
                                            ):
                                                concept_full_name = name["name"]
                                                break
                                    concept_answers = []
                                    for answer in concept["answers"]:
                                        if (
                                                answer["name"]["conceptNameType"]
                                                == Constants.FULLY_SPECIFIED.value
                                                and answer["name"]["locale"]
                                                == req.session["locale"]
                                        ):
                                            concept_answers.append(
                                                {
                                                    "uuid": answer["uuid"],
                                                    "display": answer["display"],
                                                }
                                            )
                                        else:
                                            for name in answer["names"]:
                                                if (
                                                        name["conceptNameType"]
                                                        == Constants.FULLY_SPECIFIED.value
                                                        and name["locale"]
                                                        == req.session["locale"]
                                                ):
                                                    concept_answers.append(
                                                        {
                                                            "uuid": answer["uuid"],
                                                            "display": name["display"],
                                                        }
                                                    )
                                    attrs.append(
                                        {
                                            "attributeType": {
                                                "uuid": attribute["uuid"],
                                                "name": concept_full_name,
                                                "datatype": attribute[
                                                    "datatypeClassname"
                                                ],
                                                "inputType": datatype["inputType"],
                                                "answers": concept_answers,
                                                "group": attribute["groupName"],
                                            }
                                        }
                                    )
                                except Exception:
                                    continue
                            else:
                                try:
                                    concept = mu.get_concept_by_search(
                                        req, attribute["name"]
                                    )
                                    concept_full_name = concept["display"]
                                    if (
                                            concept["name"]["conceptNameType"]
                                            != Constants.FULLY_SPECIFIED.value
                                    ):
                                        for name in concept["names"]:
                                            if (
                                                    name["conceptNameType"]
                                                    == Constants.FULLY_SPECIFIED.value
                                                    and name["locale"]
                                                    == req.session["locale"]
                                            ):
                                                concept_full_name = name["name"]
                                                break
                                    attrs.append(
                                        {
                                            "attributeType": {
                                                "uuid": attribute["uuid"],
                                                "name": concept_full_name,
                                                "datatype": attribute[
                                                    "datatypeClassname"
                                                ],
                                                "inputType": datatype["inputType"],
                                                "group": attribute["groupName"],
                                            }
                                        }
                                    )
                                except Exception:
                                    continue
                else:
                    continue
            else:
                for datatype in datatypes:
                    if datatype["value"].replace(".name", "") == attribute[
                        "datatypeClassname"
                    ].replace(".name", ""):
                        if datatype["inputType"] == "select":
                            try:
                                concept = mu.get_concept(
                                    req, attribute["datatypeConfig"]
                                )
                                concept_full_name = concept["display"]
                                if (
                                        concept["name"]["conceptNameType"]
                                        != Constants.FULLY_SPECIFIED.value
                                ):
                                    for name in concept["names"]:
                                        if (
                                                name["conceptNameType"]
                                                == Constants.FULLY_SPECIFIED.value
                                                and name["locale"] == req.session["locale"]
                                        ):
                                            concept_full_name = name["name"]
                                            break
                                concept_answers = []
                                for answer in concept["answers"]:
                                    if (
                                            answer["name"]["conceptNameType"]
                                            == Constants.FULLY_SPECIFIED.value
                                            and answer["name"]["locale"]
                                            == req.session["locale"]
                                    ):
                                        concept_answers.append(
                                            {
                                                "uuid": answer["uuid"],
                                                "display": answer["display"],
                                            }
                                        )
                                    else:
                                        for name in answer["names"]:
                                            if (
                                                    name["conceptNameType"]
                                                    == Constants.FULLY_SPECIFIED.value
                                                    and name["locale"]
                                                    == req.session["locale"]
                                            ):
                                                concept_answers.append(
                                                    {
                                                        "uuid": answer["uuid"],
                                                        "display": name["display"],
                                                    }
                                                )
                                attrs.append(
                                    {
                                        "attributeType": {
                                            "uuid": attribute["uuid"],
                                            "name": concept_full_name,
                                            "datatype": attribute["datatypeClassname"],
                                            "inputType": datatype["inputType"],
                                            "answers": concept_answers,
                                            "group": attribute["groupName"],
                                        }
                                    }
                                )
                            except Exception:
                                continue
                        else:
                            try:
                                concept = mu.get_concept_by_search(
                                    req, attribute["name"]
                                )
                                concept_full_name = concept["display"]
                                if (
                                        concept["name"]["conceptNameType"]
                                        != Constants.FULLY_SPECIFIED.value
                                ):
                                    for name in concept["names"]:
                                        if (
                                                name["conceptNameType"]
                                                == Constants.FULLY_SPECIFIED.value
                                                and name["locale"] == req.session["locale"]
                                        ):
                                            concept_full_name = name["name"]
                                            break
                                attrs.append(
                                    {
                                        "attributeType": {
                                            "uuid": attribute["uuid"],
                                            "name": concept_full_name,
                                            "datatype": attribute["datatypeClassname"],
                                            "inputType": datatype["inputType"],
                                            "group": attribute["groupName"],
                                        }
                                    }
                                )
                            except Exception:
                                continue
        if attributes_to_get is None:
            cache.set(
                f"{lab_test_type_name}_custom_attribute_types",
                zlib.compress(pickle.dumps(attrs)),
                timeout=None,
            )
        return attrs
    except Exception as e:
        raise Exception(e)


def get_result_date_if_exists(req, orderid):
    try:
        status, response = ru.get(
            req, f"commonlab/labtestorder/{orderid}", {"v": "custom:(attributes)"}
        )
        if status:
            if response:
                attribute_status, attribute_response = ru.get(
                    req,
                    f"commonlab/labtestattribute/{response[0]['uuid']}",
                    {"v": "full"},
                )
                if attribute_status:
                    result_date = attribute_response["auditInfo"]["dateCreated"]
                    return result_date
            return None
    except Exception as e:
        raise Exception(str(e))


def get_labtest_attributes(req, orderid, representation=None):
    status, response = ru.get(
        req,
        f"commonlab/labtestorder/{orderid}",
        {"v": "custom:(attributes,labTestType)"},
    )
    if representation == "FULL":
        attribute_types = get_custom_attribute_for_labresults(
            req,
            orderid,
            attributes_to_get=None,
            lab_test_type=response["labTestType"],
        )
        for attribute_type in attribute_types:
            for attribute in response["attributes"]:
                if (
                        attribute["attributeType"]["uuid"]
                        == attribute_type["attributeType"]["uuid"]
                        and attribute["valueReference"] is not None
                ):
                    attribute_type["uuid"] = attribute["uuid"]
                    attribute_type["valueReference"] = attribute["valueReference"]
        return attribute_types
    else:
        attributes_with_values = []
        attribute_types = get_custom_attribute_for_labresults(
            req,
            orderid,
            attributes_to_get=[
                attribute["attributeType"]["uuid"]
                for attribute in response["attributes"]
            ],
            lab_test_type=response["labTestType"],
        )
        for attribute in response["attributes"]:
            for attribute_type in attribute_types:
                if (
                        attribute["attributeType"]["uuid"]
                        == attribute_type["attributeType"]["uuid"]
                        and attribute["valueReference"] is not None
                ):
                    attribute_type["uuid"] = attribute["uuid"]
                    attribute_type["valueReference"] = attribute["valueReference"]
                    attributes_with_values.append(attribute_type)
        return attributes_with_values


def get_lab_test_orders_for_dashboard(req, patientuuid):
    lab_results = None
    lab_results_status, lab_results_response = ru.get(
        req,
        f"commonlab/labtestorder",
        {
            "patient": patientuuid,
            "limit": 5,
            "v": "custom:(uuid,labTestType,labReferenceNumber,order)",
        },
    )
    if lab_results_status:
        for lab_result in lab_results_response["results"]:
            attributes = get_labtest_attributes(req, lab_result["uuid"])
            lab_result.update({"attributes": attributes})
        lab_results = lab_results_response["results"]
    return lab_results
