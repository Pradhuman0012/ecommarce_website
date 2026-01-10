from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from orders.models import Order, OrderHistory
from reportlab.lib.pagesizes import mm
from .models import Recipe
from core.decorators import staff_required

@staff_required
def print_recipe(request, recipe_id):
    """
    Prints a single Kitchen or Barista recipe
    in 80mm thermal format.
    """

    recipe = get_object_or_404(
        Recipe.objects.prefetch_related("items", "order"),
        id=recipe_id,
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline"

    width = 80 * mm
    height = 160 * mm

    p = canvas.Canvas(response, pagesize=(width, height))
    y = height - 10 * mm

    def line(text: str) -> None:
        nonlocal y
        p.drawString(5 * mm, y, text)
        y -= 5 * mm

    # ---------- HEADER ----------
    line(f"{recipe.station} ORDER")
    line("-" * 20)
    line(f"Order #{recipe.order.id}")
    line("-" * 20)

    # ---------- ITEMS ----------
    for item in recipe.items.all():
        line(f"{item.item_name} x{item.quantity}")
        if item.notes:
            line(f"  * {item.notes}")

    # ---------- FOOTER ----------
    line("-" * 20)
    line("Thank You")

    p.showPage()
    p.save()

    return response

@staff_required
def order_history_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("bill"),
        id=order_id
    )

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
    qs = (
        Order.objects
        .select_related("bill")
        .order_by("-created_at")
    )
    print("qs",qs)
    for order in qs:
        print("order",order)
    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(customer_name__icontains=q) |
            Q(id__icontains=q) |
            Q(bill__bill_number__icontains=q)
        )

    return render(
        request,
        "orders/order_history_list.html",
        {
            "orders": qs,
        },
    )