from django.urls import path
from . import views

urlpatterns = [
    path("login", views.render_login, name="login"),
    path("", views.render_search_patients_view, name="searchPatientsView"),
    path("locations", views.get_locations, name="locations"),
    path("concepts", views.get_concepts, name="concepts"),
    path("concepts/<str:uuid>", views.get_concepts, name="conceptsbyuuid"),
    path("search", views.search_patients_query, name="search"),
    path(
        "tbdashboard/patient/<str:uuid>",
        views.render_patient_dashboard,
        name="dashboard",
    ),
    path(
        "<str:mdrtb>/dashboard/patient/<str:uuid>",
        views.render_patient_dashboard,
        name="mdrdashboard",
    ),
    path("report", views.index, name="report"),
    path("enrollpatient", views.render_enroll_patient, name="enrollPatient"),
    path(
        "patient/<str:uuid>/dotsprogramenroll",
        views.render_enroll_in_dots_program,
        name="dotsprogramenroll",
    ),
    path(
        "patient/<str:uuid>/mdrtbprogramenrollment",
        views.render_enroll_patient_in_mdrtb,
        name="mdrtbprogramenroll",
    ),
    path(
        "patient/<str:uuid>/editdotsprogram/<str:programid>",
        views.render_edit_dots_program,
        name="editdotsprogram",
    ),
    path(
        "patient/<str:uuid>/editmdrtbprogram/<str:programid>",
        views.render_edit_mdrtb_program,
        name="editmdrtbprogram",
    ),
    path(
        "patient/<str:uuid>/enrolledprograms",
        views.render_enrolled_programs,
        name="enrolledprograms",
    ),
    path(
        "patient/<str:patientuuid>/transferout",
        views.render_transferout_form,
        name="transferout",
    ),
    path(
        "patient/<str:patientuuid>/transferout/<str:formid>",
        views.render_edit_transferout_form,
        name="edittransferout",
    ),
    path(
        "transferout/<str:formid>",
        views.render_delete_transferout_form,
        name="deletetransferout",
    ),
    path(
        "patient/<str:patientid>/drugresistense",
        views.render_drug_resistence_form,
        name="drugresistanse",
    ),
    path(
        "patient/<str:patientid>/drugresistense/<str:formid>",
        views.render_edit_drug_resistence_form,
        name="editdrugresistanse",
    ),
    path(
        "drugresistense/<str:formid>",
        views.render_delete_drug_resistence_form,
        name="deletedrugresistanse",
    ),
    path("profile", views.render_user_profile, name="profile"),
    path("patient/<str:uuid>/tb03", views.render_tb03_form, name="tb03"),
    path(
        "patient/<str:uuid>/tb03/<str:formid>",
        views.render_edit_tb03_form,
        name="edittb03",
    ),
    path("tb03/<str:formid>", views.render_delete_tb03_form, name="deletetb03"),
    path("patient/<str:uuid>/form89", views.render_form_89, name="form89"),
    path(
        "patient/<str:uuid>/form89/<str:formid>",
        views.render_edit_form_89,
        name="editform89",
    ),
    path("form89/<str:formid>", views.render_delete_form_89, name="deleteform89"),
    path("patient/<str:patientid>/regimen", views.render_regimen_form, name="regimen"),
    path(
        "patient/<str:patientid>/regimen/<str:formid>",
        views.render_edit_regimen_form,
        name="editregimen",
    ),
    path(
        "regimen/<str:formid>", views.render_delete_regimen_form, name="deleteregimen"
    ),
    path(
        "patient/<str:patientid>/adverseevents",
        views.render_adverse_events_form,
        name="adverseevents",
    ),
    path(
        "adverseevents/<str:formid>",
        views.render_delete_adverse_events_form,
        name="deleteadverseevents",
    ),
    path(
        "patient/<str:patientid>/adverseevents/<str:formid>",
        views.render_edit_adverse_events_form,
        name="editadverseevents",
    ),
    path("patient/<str:uuid>/tb03u", views.render_tb03u_form, name="tb03u"),
    path(
        "patient/<str:uuid>/tb03u/<str:formid>",
        views.render_edit_tb03u_form,
        name="edittb03u",
    ),
    path("tb03u/<str:formid>", views.render_delete_tb03u_form, name="deletetb03u"),
    path("patientlist", views.render_patient_list, name="patientlist"),
    # Reporting Urls
    path("tb03export", views.render_tb03_report_form, name="tb03export"),
    path("tb03results", views.render_tb03_report, name="tb03Results"),
    path("tb03uexport", views.render_tb03u_report_form, name="tb03uexport"),
    path("tb03uresults", views.render_tb03u_report, name="tb03uResults"),
    path("form89export", views.render_form89_report_form, name="form89export"),
    path("form89results", views.render_form89_report, name="form89results"),
    path("tb08export", views.render_tb08_report_form, name="tb08export"),
    path("tb08results", views.render_tb08_report, name="tb08results"),
    path("tb08uexport", views.render_tb08u_report_form, name="tb08uexport"),
    path("tb08uresults", views.render_tb08u_report, name="tb08uresults"),
    path("tb07uexport", views.render_tb07u_report_form, name="tb07uexport"),
    path("tb07uresults", views.render_tb07u_report, name="tb07uresults"),
    # CommonLab Urls
    path(
        "commonlab/managetesttypes",
        views.render_manage_test_types,
        name="managetesttypes",
    ),
    path(
        "commonlab/fetchattributes",
        views.fetch_attributes,
        name="fetchattributes",
    ),
    path("commonlab/addtesttypes", views.render_add_test_type, name="addtesttype"),
    path(
        "commonlab/edittesttype/<str:uuid>",
        views.render_edit_test_type,
        name="edittesttype",
    ),
    path(
        "commonlab/patient/<str:uuid>/addlabtest",
        views.render_add_lab_test,
        name="addlabtest",
    ),
    path(
        "commonlab/patient/<str:patientid>/laborder/<str:orderid>/editlabtest",
        views.render_edit_lab_test,
        name="editlabtest",
    ),
    path(
        "commonlab/patient/<str:patientid>/laborder/<str:orderid>/dellabtest",
        views.render_delete_lab_test,
        name="dellabtest",
    ),
    path(
        "commonlab/labtest/<str:uuid>/manageattributes",
        views.render_manageAttributes,
        name="manageattr",
    ),
    path(
        "commonlab/labtest/<str:uuid>/addattributes",
        views.render_addattributes,
        name="addattr",
    ),
    path(
        "commonlab/labtest/<str:testid>/editattributes/<str:attrid>",
        views.render_editAttribute,
        name="editattr",
    ),
    path(
        "commonlab/patient/<str:uuid>/managetestorders",
        views.render_managetestorders,
        name="managetestorders",
    ),
    path(
        "commonlab/order/<str:orderid>/managesamples",
        views.render_managetestsamples,
        name="managetestsamples",
    ),
    path(
        "commonlab/order/<str:orderid>/addsample",
        views.render_add_test_sample,
        name="addtestsample",
    ),
    path(
        "commonlab/order/<str:orderid>/sample/<str:sampleid>/editsample",
        views.render_edit_test_sample,
        name="edittestsample",
    ),
    path(
        "commonlab/order/<str:orderid>/sample/<str:sampleid>/deletesample",
        views.render_delete_sample,
        name="deletesample",
    ),
    path(
        "commonlab/retiretesttype/<str:uuid>",
        views.render_retire_test_type,
        name="retiretesttype",
    ),
    path(
        "commonlab/order/<str:orderid>/sample/<str:sampleid>/changesamplestatus",
        views.render_change_sample_status,
        name="changesamplestatus",
    ),
    path(
        "commonlab/order/<str:orderid>/addtestresults",
        views.render_add_test_results,
        name="addtestresults",
    ),
    path("logout", views.render_logout, name="logout"),
]
