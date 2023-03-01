import utilities.restapi_utils as ru


class SessionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if session_id is present in session
        if not request.session.get("session_id"):
            ru.clear_session(request)
        response = self.get_response(request)
        return response
