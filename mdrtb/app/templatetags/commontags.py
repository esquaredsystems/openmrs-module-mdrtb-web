from django.template.defaulttags import register
from datetime import datetime
from dateutil import parser


@register.filter
def get_datenow(placeholder):
    labref = str(datetime.now())
    return labref[:23]


@register.filter
def iso_to_normal_date(date):
    return str(parser.isoparse(date)).split(' ')[0]


@register.filter
def get_encounter_name(name):
    return name[:len(name)-10]

@register.filter
def get_id_from_name(name):
    return name.split('-')[0]