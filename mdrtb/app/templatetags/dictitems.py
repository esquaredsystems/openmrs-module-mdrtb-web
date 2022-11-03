from django.template.defaulttags import register
from utilities import metadata_util as mu


@register.filter
def get_message(message_code, locale,default=None):
    if locale == 'en':
        value = mu.get_message(message_code)
    else:
        value = mu.get_message(message_code, locale=locale)
    return value
