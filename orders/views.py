from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from orders.models import Order, OrderHistory
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas

from billing.models import Bill
from .models import Recipe


# -----------------------------
# Queue Screen (Secondary / Ops)
# -----------------------------
def order_queue(request):
    """
    Shows pending Kitchen and Barista recipes.
    Used for monitoring / reprint / backup.
    """

    kitchen_recipes = (
        Recipe.objects
        .filter(station="KITCHEN", status="NEW")
        .prefetch_related("items", "order")
        .order_by("created_at")
    )

    barista_recipes = (
        Recipe.objects
        .filter(station="BARISTA", status="NEW")
        .prefetch_related("items", "order")
        .order_by("created_at")
    )

    return render(
        request,
        "orders/queue.html",
        {
            "kitchen_recipes": kitchen_recipes,
            "barista_recipes": barista_recipes,
        },
    )


# -----------------------------
# Print Single Recipe (KOT)
# -----------------------------
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


# -----------------------------
# Print Hub (PRIMARY UX)
# -----------------------------
def print_hub(request, bill_id):
    """
    Single counter screen to print:
    - Customer Bill
    - Kitchen Slip
    - Barista Slip
    """

    bill = get_object_or_404(Bill, id=bill_id)

    # Guaranteed correct order (OneToOne)
    order = bill.order

    kitchen_recipe = order.recipes.filter(
        station="KITCHEN"
    ).first()

    barista_recipe = order.recipes.filter(
        station="BARISTA"
    ).first()

    return render(
        request,
        "orders/print_hub.html",
        {
            "bill": bill,
            "kitchen_recipe": kitchen_recipe,
            "barista_recipe": barista_recipe,
        },
    )




def order_history_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("bill"),
        id=order_id
    )

    history = (
        OrderHistory.objects
        .filter(order=order)
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/order_history.html",
        {
            "order": order,
            "history": history,
        },
    )

def order_history_list_view(request):
    qs = (
        Order.objects
        .select_related("bill")
        .order_by("-created_at")
    )

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
        {"orders": qs},
    )