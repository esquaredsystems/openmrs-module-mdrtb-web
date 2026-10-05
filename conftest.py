"""
pytest setup. The test modules import app code (views, utilities) that reads
Django settings at import time, so Django must be configured before pytest
collects them. manage.py test does this itself; plain pytest needs it here.
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
django.setup()
