from django.template.defaulttags import register
from datetime import datetime

@register.filter
def get_datenow(placeholder):
    labref = str(datetime.now())
    return labref[:23]