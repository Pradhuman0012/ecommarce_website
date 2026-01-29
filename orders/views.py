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

    history = OrderHistory.objects.filter(order=order).order_by("-created_at")

    for h in history:
        if isinstance(h.items_snapshot, dict):
            h.items_snapshot = list(h.items_snapshot.values())

    return render(
        request,
        "orders/order_history.html",
        {
            "order": order,
            "history": history,
        },
    )


@staff_required
def order_history_list_view(request):
    qs = Order.objects.select_related("bill").order_by("-created_at")
    print("qs", qs)
    for order in qs:
        print("order", order)
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
