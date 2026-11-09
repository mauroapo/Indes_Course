"""
Module-level permission gating for the Indes Portal.

``MODULE_PERMISSIONS`` is the single source of truth for which Django
permission unlocks which product module. Every view that belongs to a module
must be decorated with :func:`module_required`, and every new module must add
its entry here. See ``docs/architecture/permissions.md``.

Convention (do not break it):

    @login_required
    @module_required(MODULE_PERMISSIONS['cursos'])
    def some_view(request): ...

* ``login_required`` stays outermost so anonymous users are redirected to
  the login page by Django (and by ``core.middleware.AuthRequiredMiddleware``),
  not shown a 403.
* ``module_required`` raises ``PermissionDenied`` so the branded 403 handler
  runs.
* The decorator stamps ``view.module_permissions`` on the callable so the
  convention can be asserted by tests (``courses/tests_permissions.py``).
"""

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator


# Module key -> required Django permission codename (``app_label.codename``).
# Extend this dict when adding a module; never gate a view on a permission
# that is missing from here.
MODULE_PERMISSIONS = {
    'cursos': 'courses.access_courses',
    'presenca': 'courses.access_presence',
}


def user_has_module(user, module_key):
    """Return True when *user* may open the module registered as *module_key*.

    Superusers always pass. Unknown module keys fail closed.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True

    permission = MODULE_PERMISSIONS.get(module_key)
    if permission is None:
        return False
    return user.has_perm(permission)


def module_required(*perms):
    """Gate a function view behind one or more module permissions.

    Multiple permissions are combined with **all-of** semantics: the user must
    hold every permission listed. Any failure raises ``PermissionDenied``
    (403), except for anonymous users, who should already have been stopped by
    ``login_required`` / ``AuthRequiredMiddleware``.

    The wrapped callable carries ``module_permissions`` (a tuple) for
    introspection and testing.
    """
    required = tuple(perms)
    if not required:
        raise ValueError('module_required() needs at least one permission')

    def decorator(view):
        @wraps(view)
        def _wrapped(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if user is None or not user.is_authenticated:
                raise PermissionDenied('Autenticação necessária.')
            if not user.is_superuser and not user.has_perms(required):
                raise PermissionDenied(
                    'Você não tem permissão para acessar este módulo.'
                )
            return view(request, *args, **kwargs)

        _wrapped.module_permissions = required
        return _wrapped

    return decorator


class ModuleRequiredMixin:
    """Class-based-view counterpart of :func:`module_required`.

    Use as the **left-most** mixin, before ``LoginRequiredMixin`` in MRO terms
    it is applied after login handling when combined as::

        class CourseListView(ModuleRequiredMixin, LoginRequiredMixin, ListView):
            module_permissions = (MODULE_PERMISSIONS['cursos'],)
    """

    module_permissions = ()

    def dispatch(self, request, *args, **kwargs):
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            raise PermissionDenied('Autenticação necessária.')
        if not user.is_superuser and not user.has_perms(
            tuple(self.module_permissions)
        ):
            raise PermissionDenied(
                'Você não tem permissão para acessar este módulo.'
            )
        return super().dispatch(request, *args, **kwargs)


def module_required_method(*perms):
    """Apply :func:`module_required` to a CBV method (e.g. ``dispatch``)."""
    return method_decorator(module_required(*perms), name='dispatch')