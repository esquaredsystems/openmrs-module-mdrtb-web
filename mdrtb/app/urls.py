from django.urls import path
from . import views

urlpatterns = [
    path("login", views.login, name="login"),
    path("", views.search_patients_view, name="searchPatientsView"),
    path("locations", views.get_locations, name="locations"),
    path("concepts", views.get_concepts, name="concepts"),
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
        "patient/<str:uuid>/enrolledprograms",
        views.enrolled_programs,
        name="enrolledprograms",
    ),
    path(
        "patient/<str:patientuuid>/transferout",
        views.transferout_form,
        name="transferout",
    ),
    path(
        "patient/<str:patientuuid>/transferout/<str:formid>",
        views.edit_transferout_form,
        name="edittransferout",
    ),
    path(
        "transferout/<str:formid>",
        views.delete_transferout_form,
        name="deletetransferout",
    ),
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
    path("patientlist", views.patient_list, name="patientlist"),
    # Reporting Urls
    path("tb03export", views.tb03_report_form, name="tb03export"),
    path("tb03results", views.tb03_report, name="tb03Results"),
    path("tb03uexport", views.tb03u_report_form, name="tb03uexport"),
    path("tb03uresults", views.tb03u_report, name="tb03uResults"),
    path("form89export", views.form89_report_form, name="form89export"),
    path("form89results", views.form89_report, name="form89results"),
    path("tb08export", views.tb08_report_form, name="tb08export"),
    path("tb08results", views.tb08_report, name="tb08results"),
    path("tb08uexport", views.tb08u_report_form, name="tb08uexport"),
    path("tb08uresults", views.tb08u_report, name="tb08uresults"),
    path("tb07uexport", views.tb07u_report_form, name="tb07uexport"),
    path("tb07uresults", views.tb07u_report, name="tb07uresults"),
    # CommonLab Urls
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
