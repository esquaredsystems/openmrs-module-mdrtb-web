from django.template.defaulttags import register
from datetime import datetime
from dateutil import parser
import json
from utilities import metadata_util as mu


@register.filter
def get_datenow(placeholder):
    date_time_now = str(datetime.now())
    return date_time_now


@register.filter
def get_specimem_identifier(placeholder):
    date_time_now = str(datetime.now())
    date_time_short = date_time_now[:23]
    labref = "".join(filter(str.isalnum, date_time_short))
    return labref[2 : len(labref)]


@register.filter
def get_lab_reference_num(placeholder):
    date_time_now = str(datetime.now())
    date_time_short = date_time_now[:23]
    labref = "".join(filter(str.isalnum, date_time_short))
    return labref[2 : len(labref) - 2]


@register.filter
def iso_to_normal_date(date):
    if date:
        normal_date = str(parser.isoparse(date)).split(" ")[0]
        splitted = normal_date.split("-")
        splitted.reverse()
        normal_date = ".".join(splitted)
        return normal_date
    else:
        return None


@register.filter
def get_encounter_name(name):
    return name[: len(name) - 10]


@register.filter
def get_id_from_name(name):
    return name.split("-")[0]


@register.filter
def get_year(date):
    return date[:4]


@register.filter
def get_range(number):
    return range(int(number))


@register.filter
def sum(a, b):
    return a + b


@register.filter
def sub(a, b):
    return a - b
