from django.shortcuts import redirect

from utilities import messages_util as msg
from utilities import restapi_utils as ru

# Paths that must stay reachable without an authenticated session.
# (WhiteNoise serves /static/ before this middleware runs; listed anyway for safety.)
EXEMPT_PATH_PREFIXES = ("/login", "/static/", "/favicon.ico", "/test/slow")


class SessionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # No OpenMRS session id in the Django session -> user is not logged in.
        # Clear any leftover session data (preserves redirect_url) and send them
        # to the login page instead of letting views render half-broken pages.
        if not request.session.get("session_id"):
            ru.clear_session(request)
            if not request.path.startswith(EXEMPT_PATH_PREFIXES):
                return redirect("login")
        else:
            # Translations are cached at login, but Redis can be restarted 
            # or the entry can expire mid-session. Without this every
            # label on the next page would render as its code.
            # One Redis read per request; REST call only when the cache is cold.
            msg.warm(request, request.session.get("locale"))
        response = self.get_response(request)
        return response
