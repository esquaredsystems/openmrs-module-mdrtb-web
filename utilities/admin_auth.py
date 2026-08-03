"""
Who is allowed to change Administration data.

Single source of truth, shared by the location and user admin screens, so the
rule can never drift between them.
"""

SYSTEM_DEVELOPER_ROLE = "System Developer"


def is_system_developer(req):
    """
    True when the logged-in user may modify administration data.

    Mirrors metadata_util.check_if_user_has_privilege: the 'admin' account is
    always allowed. Roles are matched on both "name" and "display" because
    GET /session returns roles in ref representation, which carries display
    but often no name.
    """
    logged_user = req.session.get("logged_user") or {}
    user = logged_user.get("user") or {}
    if user.get("systemId") == "admin":
        return True
    for role in user.get("roles") or []:
        if role.get("name") == SYSTEM_DEVELOPER_ROLE:
            return True
        if role.get("display") == SYSTEM_DEVELOPER_ROLE:
            return True
    return False
