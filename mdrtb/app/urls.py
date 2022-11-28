from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='home'),
    path('search', views.search_patients_query, name='search'),
    path('patient/<str:uuid>', views.patient_dashboard, name='dashboard'),
    path('concepts' , views.concepts,name='concepts'),
    path('conceptsearch', views.concepts, name='concept_search'),
    path('report', views.index, name='report'),
    path('searchpatients', views.search_patients_view, name='searchPatientsView'),
    path('enrollpatient', views.enroll_patient, name='enrollPatient'),
    path('programenroll' , views.enroll_in_dots_program,name="dotsEnroll"),
    path('transfer' , views.transfer,name='transfer'),
    path('drugresistense' , views.drug_resistence_form,name='drugresistense'),
    path('profile',views.user_profile,name='profile'),
    path('tb03' , views.tb03_form,name='tb03'),
    path('form89' , views.form_89,name='form89'),
    path('regimen' ,views.regimen_form,name='regimen'),
    path('manageadverseevents' , views.manage_adverse_events,name='manageae'),
    path('adverseevents' , views.adverse_events_form,name='adverseevents'),
    path('tb03u' , views.tb03u_form,name='tb03u'),
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
