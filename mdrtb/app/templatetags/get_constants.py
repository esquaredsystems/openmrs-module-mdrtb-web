from django.template.defaulttags import register
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.constants import Constants


@register.filter
def get_concept(name):
    return Concepts[name].value


@register.filter
def get_constant(name):
    return Constants[name].value
