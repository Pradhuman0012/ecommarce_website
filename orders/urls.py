from django.urls import path
from .views import print_recipe, order_history_view, order_history_list_view

app_name = "orders"

urlpatterns = [
    path("recipe/print/<int:recipe_id>/", print_recipe, name="print_recipe"),
    path("history/", order_history_list_view, name="order_history_list"),
    path("history/<int:order_id>/", order_history_view, name="order_history"),
]