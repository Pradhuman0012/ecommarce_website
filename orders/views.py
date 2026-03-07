from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from core.decorators import staff_required
from orders.models import Order, OrderHistory, Recipe
from utils.pdf import draw_kitchen_pdf


@staff_required
def print_recipe(request, recipe_id):
    recipe = get_object_or_404(
        Recipe.objects.prefetch_related("items", "order"),
        id=recipe_id,
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline"

    draw_kitchen_pdf(
        recipe=recipe,
        output=response,
    )
    return response


@staff_required
def order_history_view(request, order_id):
    order = get_object_or_404(Order.objects.select_related("bill"), id=order_id)
    bill = order.bill

    kot_orders = (
        Order.objects.filter(bill=bill)
        .prefetch_related("items__item", "recipes")
        .order_by("created_at")
    )

    history = list(
        OrderHistory.objects.filter(order__in=kot_orders).order_by("created_at")
    )

    if bill and history:
        current_subtotal = bill.subtotal()
        current_discount = bill.discount_amount or 0

        taxable_amount = current_subtotal - current_discount
        gst_percent = bill.gst_percentage or 0

        total_gst_amount = (taxable_amount * gst_percent) / 100

        history[0].subtotal = current_subtotal
        history[0].discount_amount = current_discount
        history[0].discount_percent = bill.discount_percent

        history[0].cgst_amount = total_gst_amount / 2
        history[0].sgst_amount = total_gst_amount / 2

        history[0].total_amount = bill.total_amount()

    return render(
        request,
        "orders/order_history.html",
        {
            "order": order,
            "kot_orders": kot_orders,
            "history": history,
            "bill": bill,
        },
    )


@staff_required
def order_history_list_view(request):
    qs = (
        Order.objects.select_related("bill")
        .filter(bill__isnull=False)  # only completed / billed orders
        .order_by("-created_at")
    )

    q = request.GET.get("q")

    if q:
        qs = qs.filter(
            Q(customer_name__icontains=q)
            | Q(id__icontains=q)
            | Q(bill__bill_number__icontains=q)
        )

    return render(
        request,
        "orders/order_history_list.html",
        {
            "orders": qs,
        },
    )
