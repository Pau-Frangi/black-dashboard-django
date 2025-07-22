from threading import local
from django.contrib.auth.models import AnonymousUser

_thread_locals = local()

def get_current_user():
    """Returns the current user from thread local storage."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """Middleware that stores the current user in thread local storage."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store user in thread locals
        _thread_locals.user = getattr(request, 'user', AnonymousUser())
        response = self.get_response(request)
        # Clean up
        delattr(_thread_locals, 'user')
        return response
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        
        return response
