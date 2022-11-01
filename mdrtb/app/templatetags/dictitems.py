from django.template.defaulttags import register
import utils.metadata_util as mu

@register.filter
def get_item(dict,key):
    return dict.get(key)

@register.filter
def get_message(dict,message_code):
    value = mu.get_message(message_code)
    return value