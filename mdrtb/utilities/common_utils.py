from pathlib import Path
from datetime import datetime, date
from dateutil.parser import parse
from bs4 import BeautifulSoup
from utilities import metadata_util as mu


def get_project_root() -> Path:
    """
    Returns the root path of the project.

    Returns:
    - Path: The root path of the project.

    """
    return Path(__file__).parent.parent


def read_properties_file(filepath, mode, encoding):
    """
    Reads a properties file and returns its contents as a list of lines.

    Parameters:
    - filepath (str): The path to the properties file.
    - mode (str): The mode in which the file should be opened ('r' for read).
    - encoding (str): The encoding to be used for reading the file.

    Returns:
    - list: A list containing the lines of the properties file.

    """
    configdata = []
    try:
        file = open(filepath, mode, encoding=encoding)
        for line in file.readlines():
            configdata.append(line)
        file.close()
        return configdata
    except Exception as e:
        return None


def calculate_age(dob):
    """
    Converts the date of birth to the age.

    Parameters:
    - dob: date of birth

    Returns:
    - int: age

    """
    age = 0
    try:
        converted_date = datetime.strptime(dob, "%m/%d/%Y").date()
        today_date = date.today()
        if today_date.month != converted_date.month:
            return (today_date.year - converted_date.year) - 1
        elif today_date.day >= converted_date.day:
            return today_date.year - converted_date.year
    except Exception as e:
        return None


def iso_to_normal(date):
    """
    Converts an ISO format date to a normal format.

    Parameters:
    - date (str): The ISO format date string.

    Returns:
    - str: The date string in normal format.

    """
    try:
        normal = date[: date.find("T")].replace("-", ".")
        return normal
    except Exception as e:
        return None


def remove_given_str_from_arr(arr=[], str=""):
    """
    Removes a given string from an array, if present.

    Parameters:
    - arr (list): The input array.
    - str (str): The string to be removed from the array.

    Returns:
    - list: The modified array with the given string removed, if present. If the string is not found,
            the original array is returned unchanged.

    """
    try:
        temp_copy = arr.copy()
        temp_copy.remove(str)
        return temp_copy
    except ValueError:
        return arr


def remove_given_str_from_obj_arr(arr, str, call=None):
    """
    Removes objects with a given string value from an array of objects.

    Parameters:
    - arr (list): The input array of objects.
    - str (str): The string value to be matched for removal.
    - call (str): Optional parameter specifying the call type.

    Returns:
    - list or str: If `call` is set to "commonlab", returns the name of the removed object.
                   Otherwise, returns the modified array with matching objects removed.

    """
    temp = arr.copy()
    removedName = None

    for item in temp[:]:
        if item.get("value") == str:
            removedName = item.get("name")
            temp.remove(item)

    if call == "commonlab":
        return removedName
    else:
        return temp


def remove_obj_from_objarr(objs, uuid_to_remove, key=None):
    """
    Removes an object from an array of objects based on a specified UUID.

    Parameters:
    - obj (list): The input array of objects.
    - uuid_to_remove (str): The UUID value to match for removal.
    - key (str): Optional parameter specifying the key to check for UUID match.

    Returns:
    - list or None: If the object is found and removed, returns the modified array of objects.
                   If the object is not found, returns None.

    """
    for item in objs[:]:
        if key and key in item and item[key] == uuid_to_remove:
            objs.remove(item)
            return objs

    return None


def date_to_sql_format(date):
    """
    Converts a date string in the format "YYYY-MM-DD" to the SQL datetime format "YYYY-MM-DD HH:MM:SS".

    Parameters:
    - date (str): The date string to be converted.

    Returns:
    - str: The converted date string in the SQL datetime format.
           If the input date string is not in the expected format, it is returned as is.

    """
    try:
        formated = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
        return formated
    except ValueError:
        return date


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        if type(string) == str:
            parse(string, fuzzy=fuzzy)
            return True
        return string
    except ValueError:
        return False


def get_months():
    """
    Returns a list of dictionaries representing the months of the year.

    Each dictionary in the list contains two key-value pairs:
    - "name": The name of the month.
    - "value": The numerical value of the month.

    Returns:
    - list: A list of dictionaries representing the months of the year.

    """
    return [
        {"name": "January", "value": 1},
        {"name": "February", "value": 2},
        {"name": "March", "value": 3},
        {"name": "April", "value": 4},
        {"name": "May", "value": 5},
        {"name": "June", "value": 6},
        {"name": "July", "value": 7},
        {"name": "August", "value": 8},
        {"name": "September", "value": 9},
        {"name": "October", "value": 10},
        {"name": "November", "value": 11},
        {"name": "December", "value": 12},
    ]


def get_quarters():
    """
    Returns the quarters in a year as integer.
    """
    return ["1", "2", "3", "4"]


def get_report_names(locale):
    reports = [
        "mdrtb.dotsreport07",
        "mdrtb.dotsreport08",
        "mdrtb.tb03Export",
        "mdrtb.tb03ExportSingleLine",
        "mdrtb.f89ExportSingleLine",
        "mdrtb.dotsdq.title",
        "mdrtb.dq.missingtb03",
        "mdrtb.tb07u",
        "mdrtb.tb08Fast",
        "mdrtb.tb03uExport",
        "mdrtb.tb03uExportSingleLine",
        "mdrtb.dq.title",
        "mdrtb.dq.missingtb03u",
        "mdrtb.patientLists",
    ]
    messages = []
    for report in reports:
        messages.append(mu.get_global_msgs(report, locale=locale))
    return messages


def get_patient_list_options(code):
    """
    Retrieves a message code based on the given code parameter.

    It searches for a matching rest_code in a predefined list of dictionaries called options
    and returns the corresponding message code by using the mu.get_global_msgs function.

    Parameters:
    - code (str): The code value to search for.

    Returns:
    - str: The message code associated with the provided code.
           Returns None if no matching code is found.

    Example:
    >>> get_patient_list_options("allenrolled")
    "mdrtb.allCasesEnrolled"

    """
    options = [
        {"rest_code": "allenrolled", "message_code": "mdrtb.allCasesEnrolled"},
        {
            "rest_code": "dotsbyregistrationgroup",
            "message_code": "mdrtb.dotsCasesByRegistrationGroup",
        },
        {"rest_code": "dotsbydrugresistance", "message_code": "mdrtb.byDrugResistance"},
        {
            "rest_code": "dotsbyanatomicalsite",
            "message_code": "mdrtb.dotsCasesByAnatomicalSite",
        },
        {
            "rest_code": "dotsbyregistrationgroupandbacteriologicalstatus",
            "message_code": "dotsPulmonaryCasesByRegisrationGroupAndBacStatus",
        },
        {"rest_code": "mdrxdrpatients", "message_code": "mdrtb.drTbPatients"},
        {
            "rest_code": "mdrsuccessfultreatmentoutcome",
            "message_code": "mdrtb.drTbPatientsSuccessfulTreatment",
        },
        {
            "rest_code": "mdrxdrwithnotreatment",
            "message_code": "mdrtb.drTbPatientsNoTreatment",
        },
        {
            "rest_code": "womenofchildbearingage",
            "message_code": "mdrtb.womenOfChildbearingAge",
        },
        {"rest_code": "menofconscriptage", "message_code": "mdrtb.menOfConscriptAge"},
        {
            "rest_code": "withconcomitantdisease",
            "message_code": "mdrtb.withConcomitantDisease",
        },
        {"rest_code": "bydwelling", "message_code": "mdrtb.byDwelling"},
        {"rest_code": "bysocprofstatus", "message_code": "mdrtb.bySocProfStatus"},
        {"rest_code": "bypopulationcategory", "message_code": "mdrtb.byPopCategory"},
        {
            "rest_code": "byplacesofdetection",
            "message_code": "mdrtb.byPlaceOfDetection",
        },
        {
            "rest_code": "bymethodofdetection",
            "message_code": "mdrtb.byMethodOfDetection",
        },
        {
            "rest_code": "bycircumstancesofdetection",
            "message_code": "mdrtb.byCircumstancesOfDetection",
        },
    ]

    for option in options:
        if option["rest_code"] == code:
            return mu.get_global_msgs(option["message_code"])


def string_to_html(html_string):
    html_doc = BeautifulSoup(html_string, "html.parser")
    return str(html_doc)
