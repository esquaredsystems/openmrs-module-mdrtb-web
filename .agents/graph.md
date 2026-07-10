# openmrs-module-mdrtb-web — Module Knowledge Graph
# Django 4.1.1 frontend — communicates with OpenMRS via REST only, NO direct DB access.
# Shared facts (domain model, concept/encounter-type/identifier UUIDs, topology): ../.agents/graph.md
# Usage + notation legend + maintenance rules: ../.agents/instructions.md
# Last updated: 2026-07-10 (theme + administration stubs)

## § MODULE LAYOUT
```
manage.py / gunicorn_config.py      # entry points (dev / prod)
app/views.py                        # 3010 lines — all view functions
app/urls.py                         # 79+ URL patterns
app/middleware.py                   # SessionCheckMiddleware
settings/settings.py                # Django config, Redis, REST URLs
utilities/restapi_utils.py          # HTTP client wrapper (ru alias in views)
utilities/patient_utils.py          # Patient CRUD & enrollment (pu alias)
utilities/forms_util.py             # TB form CRUD (fu alias)
utilities/commonlab_util.py         # Lab order/sample/result CRUD (clu alias)
utilities/metadata_util.py          # Concept/location/privilege lookup + caching (mu alias)
utilities/locations_util.py         # Location hierarchy (lu alias)
utilities/common_utils.py           # Date utils, report name lookup
resources/enums/mdrtbConcepts.py    # Concept UUID enum (full list)
resources/enums/encounterType.py    # Encounter type UUID enum
resources/enums/constants.py        # Program UUIDs, identifier types, order types
resources/enums/privileges.py       # 299 privilege name constants
static/ / templates in app/         # UI assets
tests/ + test_suite.py + pytest.ini # pytest
```

## § UTILITY CALL GRAPH (runtime)
```
views.py → ru (restapi_utils)    # all OpenMRS HTTP I/O
views.py → pu (patient_utils)    # patient search, save, enroll, dashboard
views.py → fu (forms_util)       # TB03/TB03U/Form89/etc CRUD
views.py → clu (commonlab_util)  # lab order / sample / result CRUD
views.py → mu (metadata_util)    # concept/location/privilege lookup + caching
views.py → lu (locations_util)   # location hierarchy queries
views.py → common_utils          # date formatting, report name resolution
metadata_util → redis            # concept/location cache
```

## § REST ROUTES (Django — METHOD path → view_function [→ utility alias])
```
# Auth
POST   /login                                              → render_login                     → ru.initiate_session
POST   /logout                                             → render_logout                    → ru.delete("session")
# Patient search & management
GET    /                                                   → render_search_patients_view
GET    /search                                             → search_patients_query            → ru.get("patient")
GET/POST /enrollpatient                                    → render_enroll_patient            → pu.save_patient
GET/POST /editpatient/<uuid>                               → render_edit_patient              → pu.save_patient
GET/POST /patient/<uuid>/enrolledprograms                  → render_enrolled_programs         → pu.get_enrolled_programs_by_patient
GET/POST /patient/<uuid>/dotsprogramenroll                 → render_enroll_in_dots_program    → pu.enroll_patient_in_program
GET/POST /patient/<uuid>/mdrtbprogramenrollment            → render_enroll_patient_in_mdrtb
GET/POST /patient/<uuid>/editdotsprogram/<programid>       → render_edit_dots_program
GET/POST /patient/<uuid>/editmdrtbprogram/<programid>      → render_edit_mdrtb_program
# Dashboards
GET    /tbdashboard/patient/<uuid>                         → render_patient_dashboard         # DOTS
GET    /mdrtb/dashboard/patient/<uuid>                     → render_patient_dashboard(mdrtb=True)
# TB03 form (DOTS)
GET/POST /patient/<uuid>/tb03                              → render_tb03_form                 → fu.create_update_tb03
GET/POST /patient/<uuid>/tb03/<formid>                     → render_edit_tb03_form
POST     /tb03/<formid>                                    → render_delete_tb03_form
# TB03U form (MDR-TB)
GET/POST /patient/<uuid>/tb03u                             → render_tb03u_form
GET/POST /patient/<uuid>/tb03u/<formid>                    → render_edit_tb03u_form
POST     /tb03u/<formid>                                   → render_delete_tb03u_form
# Form 89
GET/POST /patient/<uuid>/form89                            → render_form_89
GET/POST /patient/<uuid>/form89/<formid>                   → render_edit_form_89
POST     /form89/<formid>                                  → render_delete_form_89
# Transfer Out
GET/POST /patient/<patientuuid>/transferout                → render_transferout_form
GET/POST /patient/<patientuuid>/transferout/<formid>       → render_edit_transferout_form
POST     /transferout/<formid>                             → render_delete_transferout_form
# Drug Resistance
GET/POST /patient/<pid>/drugresistense                     → render_drug_resistence_form
GET/POST /patient/<pid>/drugresistense/<formid>            → render_edit_drug_resistence_form
POST     /drugresistense/<formid>                          → render_delete_drug_resistence_form
# Regimen
GET/POST /patient/<pid>/regimen                            → render_regimen_form
GET/POST /patient/<pid>/regimen/<formid>                   → render_edit_regimen_form
POST     /regimen/<formid>                                 → render_delete_regimen_form
# Adverse Events
GET/POST /patient/<pid>/adverseevents                      → render_adverse_events_form
GET/POST /patient/<pid>/adverseevents/<formid>             → render_edit_adverse_events_form
POST     /adverseevents/<formid>                           → render_delete_adverse_events_form
# Reports
GET/POST /reportform/<target>                              → render_report_form
GET      /patientlist                                      → render_patient_list
GET      /tb03results                                      → render_tb03_report
GET      /tb03singleresults                                → render_tb03_single_report
GET      /tb03uresults                                     → render_tb03u_report
GET      /tb03usingleresults                               → render_tb03u_single_report
GET      /form89results                                    → render_form89_report
GET      /tb07results                                      → render_tb07_report
GET      /tb07uresults                                     → render_tb07u_report
GET      /tb08results                                      → render_tb08_report
GET      /tb08uresults                                     → render_tb08u_report
GET      /missingtb03results                               → render_missing_tb03_report
GET      /missingtb03uresults                              → render_missing_tb03u_report
GET      /form8results                                     → render_form8_report
GET      /dotsdqresults                                    → render_dotsdq_report
GET      /mdrdqresults                                     → render_mdrdq_report
GET      /adverseeventsregister                            → render_adverse_events_register_report
GET      /quarterlyae                                      → render_quaterly_summary_ae_report
GET      /<type>/closedreports                             → render_closed_reports
GET      /viewclosedreport/<uuid>                          → render_single_closed_report
POST     /saveclosedreport                                 → save_closed_report
# CommonLab
GET/POST /commonlab/managetesttypes                        → render_manage_test_types         → clu.get_test_types
GET/POST /commonlab/addtesttypes                           → render_add_test_type             → clu.create_test_type
GET/POST /commonlab/edittesttype/<uuid>                    → render_edit_test_type
GET/POST /commonlab/retiretesttype/<uuid>                  → render_retire_test_type
GET/POST /commonlab/patient/<uuid>/addlabtest              → render_add_lab_test              → clu.create_lab_order
GET/POST /commonlab/patient/<pid>/laborder/<oid>/editlabtest  → render_edit_lab_test
POST     /commonlab/patient/<pid>/laborder/<oid>/dellabtest   → render_delete_lab_test
GET/POST /commonlab/labtest/<uuid>/manageattributes        → render_manage_attributes
GET/POST /commonlab/labtest/<uuid>/addattributes           → render_addattributes
GET/POST /commonlab/labtest/<tid>/editattributes/<aid>     → render_edit_attribute
GET/POST /commonlab/patient/<uuid>/managetestorders        → render_managetestorders
GET/POST /commonlab/order/<oid>/managesamples              → render_managetestsamples
GET/POST /commonlab/order/<oid>/addsample                  → render_add_test_sample
GET/POST /commonlab/order/<oid>/sample/<sid>/editsample    → render_edit_test_sample
POST     /commonlab/order/<oid>/sample/<sid>/deletesample  → render_delete_sample
POST     /commonlab/order/<oid>/sample/<sid>/changesamplestatus → render_change_sample_status
GET/POST /commonlab/order/<oid>/addtestresults             → render_add_test_results
POST     /commonlab/order/<oid>/submittolab                → submit_order_to_lab              → QuaLIS LIMS POST
GET      /commonlab/fetchattributes                        → fetch_attributes                 # JSON
GET      /commonlab/order/<oid>/gettestsamples             → check_if_sample_exists           # JSON
# Administration (stub pages; menu items disabled in components/nav.html — no "admin/" prefix, that's Django admin)
GET      /administration/locations                         → render_manage_locations          # stub
GET      /administration/translations                      → render_manage_translations       # stub
GET      /administration/defaults                          → render_set_defaults              # stub
# Config/Metadata endpoints
GET      /profile                                          → render_user_profile
GET      /locations                                        → get_locations                    # JSON
GET      /concepts                                         → get_concepts                    # JSON
GET      /concepts/<uuid>                                  → get_concepts                    # JSON
GET      /changelocale/<locale>                            → change_locale
```

## § AUTH FLOW
```
Login:
  POST /login → render_login → ru.initiate_session(username, password)
  → Basic Auth header → GET {REST_API_BASE_URL}session
  → OpenMRS returns: sessionId, user{uuid,roles,userProperties{locale,defaultLocation}}
  → Django session stores:
      session["session_id"]          = JSESSIONID value
      session["encoded_credentials"] = base64(username:password)
      session["logged_user"]         = full user+auth object
      session["locale"]              = userProperties.locale or "ru"
  → redirect to /

Per-request guard (app/middleware.py → SessionCheckMiddleware):
  every request → check session.get("session_id")
  missing → ru.clear_session(request) → session.flush() → redirect /login
  present → pass through

API request headers (utilities/restapi_utils.py → get_auth_headers):
  Authorization: Basic {encoded_credentials}
  Cookie: JSESSIONID={session_id}

401 from OpenMRS REST → clear_session() → redirect /login

Logout:
  POST /logout → DELETE {REST_API_BASE_URL}session → clear_session() → redirect /login

Session keys also used:
  session["redirect_url"]                    # post-submit redirect target
  session["current_patient_program_flow"]    # active patient+program context
  session["current_location"]               # user's active facility
  session["breadcrumbs"]                    # nav history
```

## § OPENMRS REST API CALLS (consumed)
```
BaseURL:  settings.REST_API_BASE_URL = "http://46.20.206.173:38080/openmrs/ws/rest/v1/"
Timeout:  30s  (settings.REST_TIMEOUT)
Wrapper:  utilities/restapi_utils.py
  get(req, endpoint, params)   → (True, response.json()) | raises on 401/error
  post(req, endpoint, data)    → (True, response.json()) | parses error["globalErrors"][0]["message"]
  delete(req, endpoint)        → (True, response_object)

Endpoints consumed:
  session                                    # auth probe
  patient?q={q}&v=full                       # search
  patient/{uuid}                             # CRUD
  person/{uuid}
  user/{uuid}
  programenrollment / programenrollment/{uuid}
  encounter / encounter/{uuid}
  mdrtb/*                                    # custom resources — list in openmrs-module-mdrtb/.agents/graph.md
  concept/{uuid}
  commonlab/labtesttype / commonlab/labtesttype/{uuid}
  commonlab/labtestorder / commonlab/labtestorder/{uuid}
  commonlab/labtestsample / commonlab/labtestsample/{uuid}

External:
  QuaLIS LIMS: POST http://46.20.206.172:8083/QuaLIS/externalorder/createExternalOrderOpenMrs
               # no auth currently; called from submit_order_to_lab
```

## § CACHE KEY PATTERNS (Redis)
```
Backend:  django.core.cache.backends.redis.RedisCache
Location: redis://redis:6379/1 (prod) | redis://127.0.0.1:6379/1 (dev)
Session:  SESSION_ENGINE = django.contrib.sessions.backends.cache
          Key pattern:  django.contrib.sessions.cache.{session_key}
          Expiry:       SESSION_EXPIRE_AT_BROWSER_CLOSE = True
Metadata: metadata_util.py caches concept/location lookups via Django cache API
          (exact key strings set inside each lookup function)
```

## § DJANGO SETTINGS (settings/settings.py)
```
REST_API_BASE_URL     = "http://46.20.206.173:38080/openmrs/ws/rest/v1/"  # hardcoded
QUALIS_API_BASE_URL   = "http://46.20.206.172:8083/QuaLIS/"               # hardcoded
QUALIS_API_CREDENTAILS= "username:password"                               # hardcoded, not env var
REST_TIMEOUT          = 30
TIME_ZONE             = "Asia/Dushanbe"
REDIS_LOCATION        = env("REDIS_LOCATION", default="redis://127.0.0.1:6379/1")
CORS_ALLOWED_ORIGINS  = ["http://46.20.206.173:38080","http://127.0.0.1:8080"]
DEBUG                 = True   # change for prod
```

## § UI THEME / STYLE MIGRATION (Tailwind → Bootstrap, plan: style_migration_plan.txt)
```
Load order (base.html): styles.css (Tailwind build) → bootstrap.min.css → select2.min.css → theme.css (wins)
theme.css  app/static/app/css/theme.css   # clinical-white minimalist layer: white bg, 1px borders,
                                          # brand blue #2D9CDB accent, 150ms transitions, CSS vars --brand-*
Migrated pages (no Tailwind classes):  login.html (.login-* classes), search_patients.html,
                                       components/header.html, components/nav.html
  header.html   → .header-link (hover pill)
  nav.html      → .app-menubar (left-aligned full-width menubar, included per-page by:
                  search_patients.html, admin stubs, reporting/patientlist_report_form.html,
                  reporting/report_form_base.html (shared by ALL /reportform/<target> pages —
                  DOTS/MDR/Other), reporting/closed_reports.html (dots+mdr))
                  NOTE: the individual reporting/*_report_form.html templates are DEAD CODE —
                  views.py only renders report_form_base.html + patientlist_report_form.html.
                  Report RESULT pages (report_base.html, open in new tab) have no menu by design.
                  Administration dropdown: items disabled (Bootstrap .disabled) until pages implemented
                  NOTE 2026-07-10: a "global menubar in base.html + report_base.html" attempt was REVERTED
                  by user request (design regression). Menu persistence on report pages remains an open issue.
  admin stubs   → app/templates/app/admin/{manage_locations,manage_translations,set_defaults}.html (.admin-stub-page)
  new msg keys  → mdrtb.manageTranslations, mdrtb.setDefaults, mdrtb.underConstruction (en/ru/tj)
  search page   → .patient-search-* / .patient-result-* classes (defined in theme.css only)
                  JS toggles .is-open on #search-results (no more Tailwind hidden/flex)
NOT migrated: enrolled_programs.html still uses styles.css classes (search-page-container etc.) — do not
              remove styles.css or its classes until all pages migrated.
Prod static: Dockerfile runs collectstatic; repo static/ (STATIC_ROOT) may be stale in dev.
```

## § LOCALIZATION
```
Session:   session["locale"] set at login from OpenMRS userProperties.locale (default "ru")
Switch:    GET /changelocale/<locale> → change_locale view → updates session + OpenMRS user property
Message files:
  resources/messages.properties
  resources/messages_tj.properties
  resources/messages_ru.properties
  resources/openMRS_messages*.properties
  resources/commonlab_messages.properties
```
