from django.urls import path

from .views import cms_menu

urlpatterns = [
    path("menu/", cms_menu, name="cms-menu"),
]
