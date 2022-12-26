from django.template.defaulttags import register
from utilities import metadata_util as mu
from datetime import datetime


@register.filter
def get_message(message_code, locale, default=None):
    if locale == 'en':
        value = mu.get_global_msgs(message_code, default=default)
    else:
        value = mu.get_global_msgs(
            message_code, locale=locale, default=default)
    return value


@register.filter
def get_message_openMRS(message_code, locale, default=None):
    if locale == 'en':
        value = mu.get_global_msgs(
            message_code, default=default, source='OpenMRS')
    else:
        value = mu.get_global_msgs(
            message_code, locale=locale, default=default, source='OpenMRS')
    return value


@register.filter
def get_message_commonlab(message_code, locale, default=None):
    if locale == 'en':
        value = mu.get_global_msgs(
            message_code, default=default, source='commonlab')
    else:
        value = mu.get_global_msgs(
            message_code, locale=locale, default=default, source='commonlab')
    return value
