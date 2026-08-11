"""
Template filters used across the app.

Registered on django.template.defaulttags.register, which makes them global
builtins - templates do not need a {% load %} line.

Date and number helpers live in utiltags.py; enum lookups in get_enums.py.
"""

import json

from django.template.defaulttags import register

from utilities import metadata_util as mu


@register.filter
def get_message(message_code, locale, default=None):
    """
    The translated label for a message code: {{ 'mdrtb.save'|get_message:locale }}

    The lookup itself lives in utilities/messages_util.py, which reads the
    Redis-cached message_properties table. Falls back to English, then to the
    code itself, so a missing translation shows on screen instead of a blank.
    """
    return mu.get_global_msgs(message_code, locale=locale, default=default)


@register.filter
def get_dict_item_by_key(key, result_dict):
    """
    A dict value by key: {{ key|get_dict_item_by_key:some_dict }}

    Django templates cannot subscript a dict with a variable key, hence this.
    Returns "" for a missing key rather than raising.
    """
    return result_dict.get(key, "")


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
