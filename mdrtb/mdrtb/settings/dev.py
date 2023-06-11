from .base import *

SECRET_KEY = "myitnu=(*35g9jf8arh2we$l!3+20c=)s0^52mqo5+aw6d50wg"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
REST_API_BASE_URL = "http://46.20.206.173:38080/openmrs/ws/rest/v1/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "../mdrtb/logs/django.log",
            "formatter": "simple"

        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple"

        }

    },
    "formatters": {
        "simple": {
            "format": "%(levelname)s, when = %(asctime)s, where = %(module)s.%(funcName)s, line_no = %(lineno)d, message = %(message)s",
        },
    },
    "loggers": {
        "django": {
            "level": "INFO",
            "handlers": ["file", "console"]
        }
    }
}
