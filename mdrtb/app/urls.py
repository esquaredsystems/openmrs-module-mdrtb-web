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
    path('programenroll' , views.enroll_in_dots_program,name="dotsEnroll"),
    path('profile',views.user_profile,name='profile'),
    path('tb03' , views.tb03_form,name='tb03'),
    path('logout', views.logout, name='logout'),
    path('patientlist', views.patientList, name='patientlist'),
    path('commonlab/managetesttypes' , views.manage_test_types,name='managetesttypes'),
    path('commonlab/fetchattributes' , views.fetch_attributes , name = 'fetchattributes'),
    path('commonlab/addtesttypes' , views.add_test_type ,name='addtesttype'),
    path('commonlab/edittesttype/<str:uuid>',views.edit_test_type,name='edittesttype'),
    path('commonlab/labtest/<str:uuid>/manageattributes',views.manageAttributes,name='manageattr'),
    path('commonlab/labtest/<str:uuid>/addattributes' , views.addattributes,name='addattr'),
    path('commonlab/editattributes/<str:uuid>' , views.editAttribute,name='editattr'),
    path('commonlab/managetestorders' , views.managetestorders,name='managetestorders'),
    path('commonlab/managetestsamples' , views.managetestsamples,name='managetestsamples'),
    path('commonlab/retiretesttype/<str:uuid>', views.retire_test_type,name='retiretesttype')



]
