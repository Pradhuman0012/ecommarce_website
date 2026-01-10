from functools import wraps
from typing import Callable

from django.http import HttpRequest, HttpResponseForbidden
from django.shortcuts import redirect


def login_required_project() -> Callable:
    """
    Enforces authentication globally.
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("authentication:login")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def permission_required_project(permission: str) -> Callable:
    """
    Enforces permission-based access.
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("authentication:login")

            if not request.user.has_perm(permission):
                return HttpResponseForbidden("Access denied")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


from django.core.exceptions import PermissionDenied
from functools import wraps

def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper

