from django.shortcuts import redirect
from django.conf import settings


class AuthRequiredMiddleware:
    """Middleware to require authentication for all views except login/signup."""
    
    EXEMPT_URLS = [
        '/login/',
        '/signup/',
        '/forgot-password/',  # Password reset flow
        '/favicon.ico',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Check if the path is exempt
            path = request.path_info
            is_exempt = any(path.startswith(url) for url in self.EXEMPT_URLS)
            
            if not is_exempt:
                # Redirect to login with next parameter
                return redirect(f'{settings.LOGIN_URL}?next={path}')
        
        response = self.get_response(request)
        return response
