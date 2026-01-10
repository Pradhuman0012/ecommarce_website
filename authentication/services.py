from typing import Optional

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest


def authenticate_user(
    request: HttpRequest,
    username: str,
    password: str,
) -> Optional[User]:
    """
    Authenticate and log in a user.
    """
    user = authenticate(request, username=username, password=password)
    if not user:
        return None

    login(request, user)
    return user


def logout_user(request: HttpRequest) -> None:
    """
    Logout current user.
    """
    logout(request)


def _post_login_redirect(user):
    if user.is_superuser:
        return "dashboard:home"
    if user.is_staff:
        return "billing:create_bill"
    return "home:home"
