from django.urls import path

from home import views

app_name = "home"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("category/<int:pk>/", views.category_items, name="category_items"),
    path("search/", views.search_items, name="search"),
    path("about/", views.about_view, name="about"),
    path("menu/", views.menu_display, name="menu_display"),
]
