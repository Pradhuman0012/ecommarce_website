from django.shortcuts import render
from django.utils.timezone import localdate
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from decimal import Decimal

from billing.models import Bill, BillItem


def dashboard_home(request):
    today = localdate()

    bills = Bill.objects.filter(created_at__date=today)

    total_bills = bills.count()
    total_sales = Decimal("0.00")
    total_discount = Decimal("0.00")
    total_gst = Decimal("0.00")

    for bill in bills:
        total_sales += bill.total_amount()
        total_discount += bill.discount_amount
        total_gst += bill.gst_amount()

    # ---------- AGGREGATES ----------
    total_qty = (
        BillItem.objects
        .filter(bill__in=bills)
        .aggregate(qty=Sum("quantity"))["qty"]
        or 0
    )

    avg_bill = (
        total_sales / total_bills
        if total_bills > 0
        else Decimal("0.00")
    )

    # ---------- TOP ITEMS ----------
    revenue_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )

    top_items = (
        BillItem.objects
        .filter(bill__in=bills)
        .values("item__name")
        .annotate(
            qty=Sum("quantity"),
            revenue=Sum(revenue_expr)
        )
        .order_by("-qty")[:5]
    )

    # ---------- STATUS (MEANINGFUL) ----------
    if total_bills == 0:
        status = "No Sales Today"
    elif total_sales < 1000:
        status = "Slow Day"
    elif total_sales < 5000:
        status = "Normal Day"
    else:
        status = "Busy Day"

    return render(request, "dashboard/index.html", {
        "today": today,
        "total_sales": total_sales,
        "total_bills": total_bills,
        "total_discount": total_discount,
        "total_gst": total_gst,
        "total_qty": total_qty,
        "avg_bill": avg_bill,
        "top_items": top_items,
        "status": status,
    })