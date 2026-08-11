"""
User administration helpers (Administration -> Manage Users).

An OpenMRS login is three linked records, and this module keeps them in step:

    person   - the human being (names, gender, birthdate)
    user     - the login (username, password, roles, user properties)
    provider - what encounters are attributed to; its identifier MUST equal
               the username, per the project requirement

Creation therefore runs person -> user -> provider. If the user step fails the
freshly created person is voided again, so a failed attempt does not leave an
orphan person behind. See create_user().

All REST traffic goes through utilities/rest_admin.py: real OpenMRS validation
messages ("Username is already in use") reach the user, and every list endpoint
is paged under the server's absolute-limit cap.
"""

import logging
from urllib.parse import quote

from utilities.rest_admin import (
    SessionExpired,  # noqa: F401  (re-exported for the views)
    get_all_pages,
    rest_delete,
    rest_get,
    rest_post,
)

logger = logging.getLogger("django")

# v=full gives username, systemId, retired, person (with names/gender/birthdate),
# roles and userProperties in one call.
USER_REP = "full"

# OpenMRS ships these two; they are assigned automatically and are not
# meaningful choices when creating a login, so they are hidden from the picker.
# (They still show for an existing user that somehow has them.)
IMPLICIT_ROLES = {"Anonymous", "Authenticated"}

GENDERS = [("M", "Male"), ("F", "Female")]


# ---------------------------------------------------------------- reads


def search_users(req, query=None, role_uuid=None, include_disabled=False):
    """
    Users matching the search, newest OpenMRS semantics:
      q             - matches username / system id / person name
      includeAll    - needed to see retired ("disabled") users at all
    The role filter is applied here because the REST resource has no role
    parameter.
    """
    params = {"v": USER_REP}
    if query:
        params["q"] = query
    if include_disabled:
        params["includeAll"] = "true"

    users = get_all_pages(req, "user", params)

    if role_uuid:
        users = [u for u in users if _has_role(u, role_uuid)]

    return sorted(users, key=lambda u: (u.get("username") or u.get("display") or "").lower())


def _has_role(user, role_uuid):
    return any((r or {}).get("uuid") == role_uuid for r in user.get("roles") or [])


def get_user(req, uuid):
    user = rest_get(req, f"user/{uuid}", {"v": USER_REP})
    if not user:
        return None

    person_uuid = (user.get("person") or {}).get("uuid")
    if not person_uuid:
        return user

    try:
        person = rest_get(req, f"person/{person_uuid}", {"v": "full"})
    except SessionExpired:
        raise
    except Exception as e:
        logger.warning(
            f"Could not load person {person_uuid} for user {uuid}: {e}. "
            "Demographic fields will be blank."
        )
        return user

    if not person:
        return user

    # Depending on the OpenMRS version the preferred name can itself come back
    # as a bare reference; re-fetch it so the form is never silently blank.
    names = person.get("names") or []
    index, preferred = next(
        ((i, n) for i, n in enumerate(names) if n.get("preferred")),
        (0, names[0]) if names else (None, None),
    )
    if preferred and "givenName" not in preferred and preferred.get("uuid"):
        try:
            full_name = rest_get(
                req, f"person/{person_uuid}/name/{preferred['uuid']}", {"v": "full"}
            )
            if full_name:
                names[index] = full_name
        except SessionExpired:
            raise
        except Exception as e:
            logger.warning(f"Could not expand person name {preferred.get('uuid')}: {e}")

    user["person"] = person
    return user


def get_roles(req, include_implicit=False):
    """Assignable roles, alphabetical. Retired roles are never offered."""
    roles = get_all_pages(req, "role", {"v": "full"})
    result = []
    for role in roles:
        if role.get("retired"):
            continue
        name = role.get("name") or role.get("display") or ""
        if not include_implicit and name in IMPLICIT_ROLES:
            continue
        result.append(role)
    return sorted(result, key=lambda r: (r.get("name") or r.get("display") or "").lower())


def get_provider_for_person(req, person_uuid):
    """The provider record attached to a person, or None."""
    if not person_uuid:
        return None
    providers = get_all_pages(
        req, "provider", {"v": "full", "person": person_uuid, "includeAll": "true"}
    )
    for provider in providers:
        if ((provider.get("person") or {}).get("uuid")) == person_uuid:
            return provider
    return providers[0] if providers else None


# ---------------------------------------------------------------- form mapping


def read_person_form(form):
    """Demographics half of the Add/Edit User form."""

    def clean(field):
        return (form.get(field) or "").strip() or None

    return {
        "given_name": (form.get("given_name") or "").strip(),
        "middle_name": clean("middle_name"),
        "family_name": clean("family_name"),
        "gender": (form.get("gender") or "").strip(),
        "birthdate": clean("birthdate"),
    }


def read_user_form(form):
    """Login half of the Add/Edit User form."""
    return {
        "username": (form.get("username") or "").strip(),
        "roles": form.getlist("roles") if hasattr(form, "getlist") else [],
        "default_location": (form.get("default_location") or "").strip() or None,
    }


def validate(person, user, password=None, confirm=None, require_password=False):
    """
    Returns a list of human-readable problems. Server-side validation only —
    OpenMRS enforces its own password policy on top of this.
    """
    problems = []
    if not person["given_name"]:
        problems.append("Given name is required")
    if person["gender"] not in {code for code, _ in GENDERS}:
        problems.append("Gender is required")
    if not user["username"]:
        problems.append("Username is required")
    if require_password or password:
        if not password:
            problems.append("Password is required")
        elif password != confirm:
            problems.append("Password and confirmation do not match")
    return problems


# ---------------------------------------------------------------- writes


def create_user(req, person, user, password):
    """
    Creates person -> user -> provider and returns (user_uuid, warnings).

    Rollback: if the user cannot be created, the person we just created is
    voided again so a failed attempt leaves nothing behind. The provider is
    NOT rolled back — by that point the login exists and works; a warning is
    returned instead so the operator can fix the provider record.
    """
    warnings = []

    created_person = rest_post(req, "person", _person_payload(person)) or {}
    person_uuid = created_person.get("uuid")
    if not person_uuid:
        raise Exception("OpenMRS did not return a person; user was not created.")

    try:
        created_user = (
            rest_post(req, "user", _user_payload(user, person_uuid, password)) or {}
        )
    except Exception:
        _void_person(req, person_uuid)
        raise

    user_uuid = created_user.get("uuid")

    # The provider identifier must equal the username.
    try:
        ensure_provider(req, person_uuid, user["username"])
    except SessionExpired:
        raise
    except Exception as e:
        logger.error(f"Provider creation failed for {user['username']}: {e}")
        warnings.append(
            f"The user was created but the provider record was not: {e}. "
            "Create it manually, using the username as the identifier."
        )

    return user_uuid, warnings


def save_user(req, existing, person, user):
    """
    Updates an existing user's person, login and provider.

    Returns a list of warnings. The provider identifier is kept in step with
    the username (the chosen behaviour): renaming a user renames the identifier
    that encounters are attributed to.
    """
    warnings = []
    person_uuid = (existing.get("person") or {}).get("uuid")

    if person_uuid:
        rest_post(req, f"person/{person_uuid}", _person_core_payload(person))
        _update_person_name(req, existing, person)

    rest_post(req, f"user/{existing['uuid']}", _user_update_payload(user))

    try:
        ensure_provider(req, person_uuid, user["username"])
    except SessionExpired:
        raise
    except Exception as e:
        logger.error(f"Provider sync failed for {user['username']}: {e}")
        warnings.append(f"The user was saved but the provider record was not updated: {e}")

    return warnings


def ensure_provider(req, person_uuid, username):
    """
    Guarantees a provider for this person whose identifier equals the username.
    Creates one when missing, renames it when the username changed, does
    nothing when already correct.
    """
    if not person_uuid or not username:
        return None
    provider = get_provider_for_person(req, person_uuid)
    if provider is None:
        return rest_post(
            req, "provider", {"person": person_uuid, "identifier": username}
        )
    if (provider.get("identifier") or "") != username:
        logger.info(
            f"Provider {provider['uuid']} identifier "
            f"{provider.get('identifier')!r} -> {username!r}"
        )
        return rest_post(
            req, f"provider/{provider['uuid']}", {"identifier": username}
        )
    return provider


def change_password(req, user_uuid, new_password):
    """
    Admin password reset. Requires the EDIT_USER_PASSWORDS privilege on the
    account performing it. The password is never logged.
    """
    rest_post(req, f"password/{user_uuid}", {"newPassword": new_password})


def retire_user(req, uuid, reason):
    """Disable a login. DELETE without purge = retire in OpenMRS."""
    reason = (reason or "").strip() or "Disabled from MDR-TB administration screen"
    rest_delete(req, f"user/{uuid}?reason={quote(reason)}")


def unretire_user(req, uuid):
    rest_post(req, f"user/{uuid}", {"retired": False})


# ---------------------------------------------------------------- payloads


def _person_payload(person):
    payload = {
        "names": [_name_payload(person)],
        "gender": person["gender"],
    }
    if person.get("birthdate"):
        payload["birthdate"] = person["birthdate"]
    return payload


def _person_core_payload(person):
    """Person fields that live on the person resource itself."""
    payload = {"gender": person["gender"]}
    payload["birthdate"] = person.get("birthdate")  # None clears it
    return payload


def _name_payload(person):
    payload = {"givenName": person["given_name"]}
    if person.get("middle_name"):
        payload["middleName"] = person["middle_name"]
    if person.get("family_name"):
        payload["familyName"] = person["family_name"]
    return payload


def _update_person_name(req, existing_user, person):
    """
    Names are a subresource: updating them means POSTing to the existing
    preferred name, not to the person.
    """
    person_obj = existing_user.get("person") or {}
    names = person_obj.get("names") or []
    preferred = next((n for n in names if n.get("preferred")), names[0] if names else None)
    person_uuid = person_obj.get("uuid")
    if preferred and preferred.get("uuid"):
        rest_post(
            req,
            f"person/{person_uuid}/name/{preferred['uuid']}",
            _name_payload(person),
        )
    else:
        rest_post(req, f"person/{person_uuid}/name", _name_payload(person))


def _user_payload(user, person_uuid, password):
    return {
        "username": user["username"],
        "password": password,
        "person": person_uuid,
        "roles": list(user["roles"] or []),
        "userProperties": _user_properties(user),
    }


def _user_update_payload(user):
    return {
        "username": user["username"],
        "roles": list(user["roles"] or []),
        "userProperties": _user_properties(user),
    }


def _user_properties(user):
    """
    defaultLocation drives the location preselected after login. An empty
    string clears it, which is how OpenMRS stores "not set".
    """
    return {"defaultLocation": user.get("default_location") or ""}


def _void_person(req, person_uuid):
    """Best-effort rollback; never masks the original failure."""
    try:
        rest_delete(req, f"person/{person_uuid}")
        logger.info(f"Rolled back orphan person {person_uuid} after failed user create")
    except Exception as e:
        logger.error(
            f"Could not roll back person {person_uuid} after a failed user "
            f"creation: {e}. An unused person record may remain."
        )
