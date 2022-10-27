from django.test import Client , RequestFactory
import unittest
import restapi_utils as ru


class TestRestApiUtil(unittest.TestCase):
    def test_get(self):
        factory = RequestFactory()
        req = factory.get('/search_patients/')
        actual = ru.get(req,'patient',{'q' : '24190001','v' : 'custom:(name)'})
        self.assertEquals('Регистрационный номер Дотc' , actual)
        