from django.template.defaulttags import register
from datetime import datetime
from dateutil import parser
import json
from utilities import metadata_util as mu


@register.filter
def get_datenow(placeholder):
    labref = str(datetime.now())
    return labref[:23]


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
