from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='home'),
    path('search', views.search_patients, name='search'),
    path('patient/<str:uuid>', views.patient_dashboard, name='dashboard'),
    path('report', views.index, name='report'),
    path('enroll', views.enroll, name='Enroll'),
    path('enroll2', views.enroll_two, name='Enroll2'),
    path('enroll3', views.actual_enroll, name='Enroll3'),
    path('logout', views.logout, name='logout'),
    path('patientlist', views.patientList, name='patientlist'),
    path('commonlab/managetesttypes' , views.manage_test_types,name='managetesttypes'),
    path('commonlab/fetchattributes' , views.fetch_attributes , name = 'fetchattributes'),
    path('commonlab/addtesttypes' , views.addTestTypes ,name='addtesttype'),
    path('commonlab/edittesttype/<str:uuid>',views.editTestType,name='edittesttype'),
    path('commonlab/manageattributes/<str:uuid>',views.manageAttributes,name='manageattr'),
    path('commonlab/addattributes/<str:uuid>' , views.addattributes,name='addattr'),
    path('commonlab/editattributes/<str:uuid>' , views.editAttribute,name='editattr'),
    path('commonlab/managetestorders' , views.managetestorders,name='managetestorders'),
    path('commonlab/managetestsamples' , views.managetestsamples,name='managetestsamples'),
    path('commonlab/retiretesttype/<str:uuid>', views.retireTestType,name='retiretesttype')



]
