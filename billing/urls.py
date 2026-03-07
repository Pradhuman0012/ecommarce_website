from django.urls import path

from billing import views

app_name = "billing"

urlpatterns = [
    path("create/", views.create_bill, name="create_bill"),
    path("detail/<int:bill_id>/", views.bill_detail, name="bill_detail"),
    path("pdf/<int:bill_id>/", views.bill_pdf, name="bill_pdf"),
    path("kitchen_pdf/<int:order_id>/", views.kitchen_pdf, name="kitchen_pdf"),
    path("table-order/", views.table_order_view, name="table_order"),
    path(
        "api/table-order/<int:table_id>/",
        views.get_table_order,
        name="api_get_table_order",
    ),
]
