from .base import *
import os

SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
REST_API_BASE_URL = "http://172.17.15.130:8080/openmrs/ws/rest/v1/"
SESSION_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers":True,
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
