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
utilities/locations_util.py         # ALL location logic (lu alias) — patient-facing hierarchy
                                    # (cached) + administration (writes, busts that cache)
                                    # get_locations(req, include_retired=False) is the ONE list call
                                    # get_location(req, uuid) is the ONE single-location call
utilities/users_admin_util.py       # User ADMIN screen (uau alias) — person+user+provider choreography
utilities/rest_admin.py             # SHARED admin REST: real error text + cap-aware paging (see § below)
utilities/admin_auth.py             # is_system_developer() — single source for admin write permission
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
# Administration (no "admin/" prefix — that's Django admin in settings/urls.py)
GET      /administration/locations                         → render_manage_locations          → lau  # tree + ?voided=1
GET      /administration/locations/new                     → render_create_location           → lau  # MUST precede <uuid>
GET/POST /administration/locations/<uuid>                  → render_edit_location             → lau
POST     /administration/locations/<uuid>/retire           → render_retire_location           → lau
POST     /administration/locations/<uuid>/unretire         → render_unretire_location         → lau
GET      /administration/users                             → render_manage_users              → uau  # search
GET/POST /administration/users/new                         → render_create_user               → uau
GET/POST /administration/users/<uuid>                      → render_edit_user                 → uau
GET/POST /administration/users/<uuid>/password             → render_change_password           → uau
POST     /administration/users/<uuid>/disable              → render_disable_user              → uau
POST     /administration/users/<uuid>/enable               → render_enable_user               → uau
GET      /administration/translations                      → render_manage_translations       # stub, menu item disabled
GET      /administration/defaults                          → render_set_defaults              # stub, menu item disabled
# Config/Metadata endpoints
GET      /profile                                          → render_user_profile
GET      /locations                                        → get_locations                    # JSON
GET      /concepts                                         → get_concepts                    # JSON
GET      /concepts/<uuid>                                  → get_concepts                    # JSON
GET      /changelocale/<locale>                            → change_locale
```

## § ERROR HANDLING IN VIEWS
```
views.log_and_show_error(e, req)      # message + logged traceback
views.redirect_after_error(req)       # WHERE to go when a page fails to LOAD

!! Never `return redirect("<own url name>")` from the except block that guards a
   view's RENDER path. 23 views did, so one OpenMRS 500 became an endless
   redirect loop (~25 requests in 9s against the clinical server, ending in a
   broken pipe). Use redirect_after_error(req): it prefers session["redirect_url"]
   (the referer, set when these views start) and falls back to "/" — and it never
   returns the path that just failed.
   Self-redirects inside the `if req.method == "POST"` branch are FINE and were
   left alone: a failed save re-shows the form, and the GET succeeds.
```

## § AUTH FLOW
```
Login:
  POST /login → render_login → ru.initiate_session(username, password)
  → Basic Auth header → GET {REST_API_BASE_URL}session
  → OpenMRS returns: user{uuid,roles,userProperties{locale,defaultLocation}}
  !! sessionId is NOT in the response body on current OpenMRS — it was removed
     deliberately as a security fix. The token only arrives as the JSESSIONID
     COOKIE. Reading it from the body raises KeyError: 'sessionId' and the popup
     shows the bare text "sessionId". Resolution order in initiate_session():
       body["sessionId"] (legacy servers) → cookies["JSESSIONID"] → BASIC_AUTH_ONLY
     BASIC_AUTH_ONLY is a marker keeping session_id truthy when the server sends
     no cookie; get_auth_headers() then omits the Cookie header and relies on the
     Basic credentials, which OpenMRS accepts on every call.
  → Django session stores:
      session["session_id"]          = JSESSIONID value
      session["encoded_credentials"] = base64(username:password)
      session["logged_user"]         = full user+auth object
      session["locale"]              = userProperties.locale or "ru"
  → redirect to /

Per-request guard (app/middleware.py → SessionCheckMiddleware):
  every request → check session.get("session_id")
  missing → ru.clear_session(request) → redirect /login
            EXEMPT prefixes: /login, /static/, /favicon.ico, /test/slow
  present → pass through (views still self-check via check_if_session_alive)
  NOTE: before 2026-07-10 the middleware only cleared the session and did NOT
  redirect — stale sessions could render post-login pages with REST errors.

Stale-session guard on landing page (render_search_patients_view):
  REST failure during render → ru.is_session_authenticated(req) probes GET session
  (never raises) → unauthenticated/unreachable → clear_session → redirect /login

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

## § LOCATION ADMINISTRATION (Administration → Manage Locations)
```
Util:   utilities/locations_admin_util.py  (alias lau in views.py)
        Separate from locations_util.py: admin must SEE retired locations and must
        BUST the "locations" metadata cache on every write, or the patient enrollment
        dropdowns keep serving pre-edit names for up to an hour.
Writes: lau._post/_delete (NOT ru.post) so OpenMRS validation messages reach the user.
        ru.post calls raise_for_status() before parsing the error body, so its
        detailed-error branch is unreachable and 4xx becomes a generic message.
Auth:   lau.is_system_developer(req) — systemId == "admin" OR role name/display ==
        "System Developer". Roles come from GET /session in REF rep (display only,
        no "name"), hence both keys are checked. Read = any logged-in user;
        create/edit/retire/unretire = System Developer only (server-side guard in
        every write view, plus <fieldset disabled> in the template).
REST:   GET  location?v=full[&includeAll=true]&limit=100&startIndex=N   (paged)
          !! SERVER CAP: global property webservices.rest.maxResultsAbsolute. Any
             limit above it returns HTTP 500 "Administrator has set absolute limit
             at N" — it does NOT clamp. Intended value here is 1000, but it
             reverted to the 100 default during a data migration and broke every
             list screen. Applies to EVERY list endpoint. Do not rely on the
             setting: page via rest_admin.get_all_pages(), which auto-lowers if a
             server reports a smaller cap and stops after MAX_PAGES.
          !! includeAll=true is REQUIRED: normal REST queries filter out retired
             metadata, so without it the "show voided" toggle finds nothing.
        GET  locationtag?v=full                     # tag checkboxes (no includeAll:
                                                    # retired tags must not be offered)
        GET  locationattributetype?v=full           # LEVEL: maxOccurs=1 -> single-select,
                                                    # options parsed from handlerConfig CSV
        NOTE: with v=full, nested objects (parentLocation, tags, attributes.attributeType)
              come back as REFs — uuid + display, often no "name". Code reads uuid, and
              falls back name -> display for labels.
        POST location / location/{uuid}             # core fields + tags (tags = list of uuids)
        POST/DELETE location/{uuid}/attribute[/{a}] # attributes via SUBRESOURCE, positional
                                                    # reconcile; posting the attributes array
                                                    # on update is not reliably applied
        DELETE location/{uuid}?reason=...           # retire (soft). POST {"retired":false} = restore
Tree:   lau.build_location_tree(locations, include_retired) nests via parentLocation.
        A node whose parent is filtered out is PROMOTED TO ROOT, never dropped.
        The admin view ALWAYS builds with include_retired=True, then
        lau.mark_voided_only_branches() sets node["voided_only"]. "Show voided" is
        then a pure CSS filter (.loc-tree.show-voided) — NO page reload, because the
        REST call returns retired rows regardless of the toggle, so reloading would
        cost several paged REST calls for zero new data.
        A retired node with a live descendant is NOT marked voided_only: it stays as
        a struck-through structural parent so live locations never disappear.
Form:   hidden "attribute_types" field lists rendered attribute type uuids so an
        emptied multi-select clears the attribute instead of silently keeping it.
DATA BUG (open, in the DB — not the web app):
        Locations carry DUPLICATE LEVEL attributes ("REGION REGION" badges).
        Cause: openmrs-mdrtb-etl-job/etl/location.py load_location_attribute()
        uses INSERT IGNORE with UUID() per row, so no duplicate key ever occurs
        and every ETL run appends another copy. Query 5 also re-inserts a subset
        of query 3 (both level='DISTRICT') within a single run.
        LEVEL has maxOccurs=1, so this is invalid. The tree collapses identical
        (type,value) pairs for display and logs a WARNING with the count; saving
        a location through the edit screen normalises it to one value.
        Proper fixes: make the ETL idempotent + de-dupe existing rows in SQL.
Templates: app/admin/manage_locations.html, app/admin/_location_node.html (recursive
        include), app/admin/edit_location.html. Styles: theme.css § Location administration.
```

## § USER ADMINISTRATION (Administration → Manage Users)
```
Util:   utilities/users_admin_util.py (alias uau in views.py)
Auth:   admin_auth.is_system_developer — WRITE is System Developer only, enforced in
        every write view (not just hidden in the template). Read/search: any login.
A login is THREE linked records; creation order matters:
        person  -> POST person   {names:[{givenName,middleName,familyName}], gender, birthdate}
        user    -> POST user     {username, password, person:<uuid>, roles:[uuid...],
                                  userProperties:{defaultLocation:<uuid>}}
        provider-> POST provider {person:<uuid>, identifier:<USERNAME>}
        !! PROJECT RULE: provider.identifier MUST equal user.username. ensure_provider()
           creates it when missing and RENAMES it when the username changes (chosen
           behaviour) — note encounters are attributed to that identifier.
Rollback: if POST user fails, the just-created person is voided again so a failed
        attempt leaves no orphan person. A provider failure does NOT roll back the
        user (the login already works); a warning is surfaced instead.
Read:   GET user/{uuid}?v=full returns `person` as a REFERENCE — uuid + display
        only, NO names/gender/birthdate. get_user() therefore fetches
        GET person/{uuid}?v=full separately and substitutes it in. Without that
        the edit form is blank AND save_user() cannot find the preferred
        PersonName, so it would create a SECOND name instead of updating.
Edit:   person core   -> POST person/{uuid}            {gender, birthdate}
        person name   -> POST person/{uuid}/name/{nameUuid}   (names are a SUBRESOURCE)
        user          -> POST user/{uuid}              {username, roles, userProperties}
Password: POST password/{userUuid} {"newPassword":...}  — separate screen so a password
        is never reset by accident; requires EDIT_USER_PASSWORDS. Never logged.
Disable: DELETE user/{uuid}?reason=...   Enable: POST user/{uuid} {"retired": false}
        Self-disable is blocked in the view.
Roles:  GET role?v=full (paged). Anonymous/Authenticated are hidden from the picker
        (implicit roles); retired roles never offered. Multiple roles per user.
Search: GET user?q=&v=full[&includeAll=true]. The REST resource has NO role filter —
        role filtering is applied client-side in search_users().
```

## § LOCALIZATION (rewritten 2026-08-04 — the .properties files are GONE)
```
Source of truth: the MDR-TB module's message_properties table (lang + code),
seeded by MdrtbActivator from api/src/main/resources/messages{,_ru,_tj}.properties.
Reached over REST: /ws/rest/v1/mdrtb/messageproperty
  GET  ?lang=&q=            list (q = case-insensitive substring of the CODE)
  GET|DELETE /{lang}/{code}
  POST {lang,code,message}  upsert
  !! plain @Controller, NOT a REST resource -> the maxResultsAbsolute page cap
     does not apply; one call returns all ~1,700 rows for a language.

utilities/messages_util.py (alias msg)
  lookup(code, locale, default)  <- what get_global_msgs() now calls
     Takes NO request and never makes a REST call: a page performs >1,000
     lookups, so rendering must not be able to. Order:
       cached lang -> cached en -> FILE lang -> FILE en -> default -> the code
     !! The .properties files in resources/ are the last resort and are NOT
        optional. The LOGIN PAGE cannot have a warm cache — warming needs an
        authenticated REST call — so without the files every label on it renders
        as its own code. They also cover a Redis restart or OpenMRS being down.
        Parsed ONCE per language into memory (never per lookup);
        reload_files() drops them.
        The cache is checked first, so an edit in Manage Translations still wins
        over the shipped file.
  TWO cache layers, both needed:
     Redis  ("metadata", 1h)  one compressed {code: message} map per language
     _local (60s, per worker)  in front of Redis. WITHOUT IT every label was a
            Redis round trip + zlib + unpickle: ~1,100 per page, slower than the
            files this replaced. Measured after: 1 Redis read on a cold worker,
            0 on a warm one.
     Cost of _local: an edit is visible within 60s per worker. invalidate()
     clears BOTH, and every write calls it.
  warm(req, locale)   fills Redis; called at login next to get_all_concepts and
                      as a safety net in SessionCheckMiddleware (Redis restarts).

get_global_msgs(code, locale, default, source) keeps its signature; `source` is
accepted and IGNORED (the mdrtb/OpenMRS/commonlab files became one table), so the
~1,100 call sites and the three template filters were untouched.

ADDING A NEW LABEL now means adding it to the module bundles (so the activator
seeds it) or creating it in Administration -> Manage Translations. Editing a
.properties file in this repo no longer does anything — there are none.
```

## § LOCALIZATION (historical)
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
