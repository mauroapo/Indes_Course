from django.shortcuts import render
from django.http import FileResponse, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.views.decorators.csrf import requires_csrf_token
from courses.models import Course, Enrollment


@login_required
def home_view(request):
    """Home page with two carousels."""
    # Get user's enrolled courses
    my_enrollments = Enrollment.objects.filter(user=request.user).select_related('course')[:10]
    my_courses = [enrollment.course for enrollment in my_enrollments]
    
    # Get recent active courses
    recent_courses = Course.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    return render(request, 'core/home.html', {
        'my_courses': my_courses,
        'recent_courses': recent_courses
    })


@requires_csrf_token
def error_403(request, exception=None):
    """Branded 403 page — reached from ``PermissionDenied`` (see handler403)."""
    return render(
        request,
        '403.html',
        {'exception': exception},
        status=403,
    )


def favicon_view(request):
    """Serve the PNG favicon at /favicon.ico.

    Browsers request /favicon.ico directly. Without this view
    ``AuthRequiredMiddleware`` answered it with a 302 to the login page, which
    wasted a full HTML render on every page load. Returning the (offline) PNG
    keeps the request cheap and gives the tab a real icon.
    """
    path = finders.find('core/img/favicon-192x192.png')
    if not path:
        raise Http404('favicon not found')
    return FileResponse(open(path, 'rb'), content_type='image/png')


def healthcheck(request):
    """Simple healthcheck endpoint."""
    return JsonResponse({'status': 'healthy'})