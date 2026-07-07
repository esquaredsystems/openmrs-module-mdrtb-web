import os

import django

# Several test modules (utilities/test_commonutitls.py, utilities/test_metadata_util.py,
# ...) import Django-backed utilities without configuring Django themselves, relying on
# some other test module having already called django.setup() first. Under pytest-xdist
# that's whichever test file a worker happens to import first, which isn't guaranteed -
# so those modules would intermittently fail with "settings are not configured" depending
# on scheduling. Configuring Django once here, before any test module is collected,
# makes that no longer order-dependent.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")
django.setup()
