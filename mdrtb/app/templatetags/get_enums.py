from django.template.defaulttags import register
from resources.enums.mdrtbConcepts import Concepts
from resources.enums.constants import Constants
from resources.enums.privileges import Privileges


@register.filter
def get_concept(name):
    return Concepts[name].value


@register.filter
def get_constant(name):
    return Constants[name].value


@register.filter
def get_privileges(name):
    return Privileges[name].value

@register.filter
def get_conept_by_uuid(uuid):
    return Concepts(uuid).name