from django.test import TestCase
import restapi_utils as ru

class TestRestApiUtil(TestCase):
    def test_get(self):
        actual = ru.get('patient')