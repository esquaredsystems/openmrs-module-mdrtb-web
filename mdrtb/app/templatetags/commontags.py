from django.template.defaulttags import register
import json


@register.filter
def get_encounter_name(name):
    return name[: len(name) - 10]


@register.filter
def get_encounter_date(name):
    return name[len(name) - 10 :]


@register.filter
def get_id_from_name(name):
    return name.split("-")[0]


@register.filter
def parse_json(jsonstring):
    parsed_json = json.loads(jsonstring)
    return list(parsed_json)


@register.filter
def get_year(date):
    return date[:4]
