from django.urls import path
from billing import views

app_name = "billing"

urlpatterns = [
    path("create/", views.create_bill, name="create_bill"),
    path("detail/<int:bill_id>/", views.bill_detail, name="bill_detail"),
    path("pdf/<int:bill_id>/", views.bill_pdf, name="bill_pdf"),
]