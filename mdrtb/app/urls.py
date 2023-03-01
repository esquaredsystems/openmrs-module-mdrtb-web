from django.urls import path
from . import views

urlpatterns = [
    path("login", views.login, name="login"),
    path("", views.search_patients_view, name="searchPatientsView"),
    path("locations", views.get_locations, name="locations"),
    path("search", views.search_patients_query, name="search"),
    path("tbdashboard/patient/<str:uuid>", views.patient_dashboard, name="dashboard"),
    path(
        "<str:mdrtb>/dashboard/patient/<str:uuid>",
        views.patient_dashboard,
        name="mdrdashboard",
    ),
    path("report", views.index, name="report"),
    path("enrollpatient", views.enroll_patient, name="enrollPatient"),
    path(
        "patient/<str:uuid>/dotsprogramenroll",
        views.enroll_in_dots_program,
        name="dotsprogramenroll",
    ),
    path(
        "patient/<str:uuid>/mdrtbprogramenrollment",
        views.enroll_patient_in_mdrtb,
        name="mdrtbprogramenroll",
    ),
    path(
        "patient/<str:uuid>/editdotsprogram/<str:programid>",
        views.edit_dots_program,
        name="editdotsprogram",
    ),
    path(
        "patient/<str:uuid>/editmdrtbprogram/<str:programid>",
        views.edit_mdrtb_program,
        name="editmdrtbprogram",
    ),
    path(
        "patient/<str:uuid>/program/<str:programid>",
        views.delete_program,
        name="deleteprogram",
    ),
    path(
        "patient/<str:uuid>/enrolledprograms",
        views.enrolled_programs,
        name="enrolledprograms",
    ),
    path("transfer", views.transfer, name="transfer"),
    path(
        "patient/<str:patientid>/drugresistense",
        views.drug_resistence_form,
        name="drugresistanse",
    ),
    path(
        "patient/<str:patientid>/drugresistense/<str:formid>",
        views.edit_drug_resistence_form,
        name="editdrugresistanse",
    ),
    path(
        "drugresistense/<str:formid>",
        views.delete_drug_resistence_form,
        name="deletedrugresistanse",
    ),
    path("profile", views.user_profile, name="profile"),
    path("patient/<str:uuid>/tb03", views.tb03_form, name="tb03"),
    path("patient/<str:uuid>/tb03/<str:formid>", views.edit_tb03_form, name="edittb03"),
    path("tb03/<str:formid>", views.delete_tb03_form, name="deletetb03"),
    path("patient/<str:uuid>/form89", views.form_89, name="form89"),
    path(
        "patient/<str:uuid>/form89/<str:formid>", views.edit_form_89, name="editform89"
    ),
    path("form89/<str:formid>", views.delete_form_89, name="deleteform89"),
    path("patient/<str:patientid>/regimen", views.regimen_form, name="regimen"),
    path(
        "patient/<str:patientid>/regimen/<str:formid>",
        views.edit_regimen_form,
        name="editregimen",
    ),
    path("regimen/<str:formid>", views.delete_regimen_form, name="deleteregimen"),
    #     path('patient/<str:patientid>/manageadverseevents',
    #          views.manage_adverse_events, name='manageae'),
    #     path('manageregimens', views.manage_regimens, name='manageregimens'),
    path(
        "patient/<str:patientid>/adverseevents",
        views.adverse_events_form,
        name="adverseevents",
    ),
    path(
        "adverseevents/<str:formid>",
        views.delete_adverse_events_form,
        name="deleteadverseevents",
    ),
    path(
        "patient/<str:patientid>/adverseevents/<str:formid>",
        views.edit_adverse_events_form,
        name="editadverseevents",
    ),
    path("patient/<str:uuid>/tb03u", views.tb03u_form, name="tb03u"),
    path(
        "patient/<str:uuid>/tb03u/<str:formid>", views.edit_tb03u_form, name="edittb03u"
    ),
    path("tb03u/<str:formid>", views.delete_tb03u_form, name="deletetb03u"),
    path("patientlist", views.patientList, name="patientlist"),
    path("commonlab/managetesttypes", views.manage_test_types, name="managetesttypes"),
    path("commonlab/fetchattributes", views.fetch_attributes, name="fetchattributes"),
    path("commonlab/addtesttypes", views.add_test_type, name="addtesttype"),
    path(
        "commonlab/edittesttype/<str:uuid>", views.edit_test_type, name="edittesttype"
    ),
    path(
        "commonlab/patient/<str:uuid>/addlabtest", views.add_lab_test, name="addlabtest"
    ),
    path(
        "commonlab/patient/<str:patientid>/laborder/<str:orderid>/editlabtest",
        views.edit_lab_test,
        name="editlabtest",
    ),
    path(
        "commonlab/patient/<str:patientid>/laborder/<str:orderid>/dellabtest",
        views.delete_lab_test,
        name="dellabtest",
    ),
    path(
        "commonlab/labtest/<str:uuid>/manageattributes",
        views.manageAttributes,
        name="manageattr",
    ),
    path(
        "commonlab/labtest/<str:uuid>/addattributes",
        views.addattributes,
        name="addattr",
    ),
    path(
        "commonlab/labtest/<str:testid>/editattributes/<str:attrid>",
        views.editAttribute,
        name="editattr",
    ),
    path(
        "commonlab/patient/<str:uuid>/managetestorders",
        views.managetestorders,
        name="managetestorders",
    ),
    path(
        "commonlab/order/<str:orderid>/managesamples",
        views.managetestsamples,
        name="managetestsamples",
    ),
    path(
        "commonlab/order/<str:orderid>/addsample",
        views.add_test_sample,
        name="addtestsample",
    ),
    path(
        "commonlab/retiretesttype/<str:uuid>",
        views.retire_test_type,
        name="retiretesttype",
    ),
    path(
        "commonlab/order/<str:orderid>/addtestresults",
        views.add_test_results,
        name="addtestresults",
    ),
    path("logout", views.logout, name="logout"),
]