from django.contrib import messages
import utilities.metadata_util as mu


class SessionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if session_id is present in session
        if not request.session.get('session_id'):
            redirect = request.path
            print('EXPIRED REDIRECT TO ', redirect)
            request.session.flush()
            messages.error(request, mu.get_global_msgs(
                'auth.session.expired', source='OpenMRS'))
            request.session['redirect_url'] = redirect
        response = self.get_response(request)
        return response
