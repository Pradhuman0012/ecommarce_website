from django.urls import path

from . import views

app_name = "administration"

urlpatterns = [
    path("", views.admin_dashboard, name="dashboard"),
    path("cash/", views.cash_counter_view, name="cash_counter"),
    path("staff/", views.staff_list_view, name="staff_list"),
    path("expenses/", views.expense_list_view, name="expense_list"),
    path("customers/", views.customer_list_view, name="customer_list"),
    path(
        "customers/<int:customer_id>/",
        views.customer_detail_view,
        name="customer_detail",
    ),
    path("staff/<int:staff_id>/", views.staff_detail_view, name="staff_detail"),
    path("api/customer-lookup/", views.get_customer_by_phone, name="customer_lookup"),
    path("api/customer-search/", views.search_customers, name="customer_search"),
]
