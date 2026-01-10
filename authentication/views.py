from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .services import authenticate_user, logout_user, _post_login_redirect


def login_view(request: HttpRequest) -> HttpResponse:
    """
    Login screen controller.
    """
    if request.user.is_authenticated:
        return redirect(_post_login_redirect(request.user))

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = authenticate_user(request, username, password)
        if user:
            return redirect(_post_login_redirect(user))

        return render(
            request,
            "authentication/login.html",
            {"error": "Invalid credentials"},
        )

    return render(request, "authentication/login.html")


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout_user(request)
    return redirect("authentication:login")