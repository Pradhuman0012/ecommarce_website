from django.urls import path

from dashboard.views import dashboard_home

app_name = "dashboard"

urlpatterns = [
    path("", dashboard_home, name="home"),
]
