from pathlib import Path
import mimetypes
import os
import dotenv
import base64


dotenv.load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "y^ie20@y6-(23i!+m(-&*w6&#&j()5pe4k$klp6*p&95-d*x$%"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app.apps.AppConfig",
    "corsheaders",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = ["http://46.20.206.173:38080", "http://46.20.206.172:8083", "http://127.0.0.1:8080"]

ROOT_URLCONF = "mdrtb.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "app/templates/app/"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mdrtb.wsgi.application"


SESSIONS_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    }
}


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Dushanbe"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "app/static"
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TAILWIND_APP_NAME = "theme"
INTERNAL_IPS = [
    "127.0.0.1",
]


# CHANGE THIS
#REST_API_BASE_URL = "http://46.20.206.173:38080/openmrs/ws/rest/v1/"
REST_API_BASE_URL = "http://127.0.0.1:8080/openmrs/ws/rest/v1/"
QUALIS_API_BASE_URL = "http://46.20.206.172:8083/QuaLIS/"
QUALIS_API_CREDENTAILS = "username:password"

mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("text/html", ".html", True)
mimetypes.add_type("text/javascript", ".js", True)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "../mdrtb/logs/django.log",
            "formatter": "simple",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "formatters": {
        "simple": {
            "format": "%(levelname)s, when = %(asctime)s, where = %(module)s.%(funcName)s, line_no = %(lineno)d, message = %(message)s",
        },
    },
    "loggers": {"django": {"level": "INFO", "handlers": ["file", "console"]}},
}
