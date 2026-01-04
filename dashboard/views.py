from django.shortcuts import render
from django.utils.timezone import localdate
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from datetime import date
from decimal import Decimal

from billing.models import Bill, BillItem


def dashboard_home(request):
    mode = request.GET.get("mode", "day")

    today = localdate()
    bills = Bill.objects.none()
    label = ""

    # ----------------------------
    # DAY FILTER
    # ----------------------------
    if mode == "day":
        selected_date = request.GET.get("date")

        if selected_date:
            selected_date = date.fromisoformat(selected_date)
        else:
            selected_date = today

        bills = Bill.objects.filter(
            created_at__date=selected_date
        )

        label = selected_date.strftime("%d %b %Y")

    # ----------------------------
    # MONTH FILTER
    # ----------------------------
    elif mode == "month":
        selected_month = int(request.GET.get("month", today.month))
        selected_year = int(request.GET.get("year", today.year))

        bills = Bill.objects.filter(
            created_at__year=selected_year,
            created_at__month=selected_month,
        )

        label = f"{date(selected_year, selected_month, 1).strftime('%B %Y')}"

    # ----------------------------
    # YEAR FILTER
    # ----------------------------
    elif mode == "year":
        selected_year = int(request.GET.get("year", today.year))

        bills = Bill.objects.filter(
            created_at__year=selected_year
        )

        label = str(selected_year)

    # ----------------------------
    # CALCULATIONS
    # ----------------------------
    total_bills = bills.count()
    total_sales = Decimal("0.00")
    total_discount = Decimal("0.00")
    total_gst = Decimal("0.00")

    for bill in bills:
        total_sales += bill.total_amount()
        total_discount += bill.discount_amount
        total_gst += bill.gst_amount()

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

    return render(request, "dashboard/index.html", {
        "mode": mode,
        "label": label,
        "total_sales": total_sales,
        "total_bills": total_bills,
        "total_discount": total_discount,
        "total_gst": total_gst,
        "total_qty": total_qty,
        "avg_bill": avg_bill,
        "top_items": top_items,

        # REQUIRED FOR TEMPLATE
        "months": range(1, 13),
        "selected_date": request.GET.get("date", today.isoformat()),
        "selected_month": int(request.GET.get("month", today.month)),
        "selected_year": int(request.GET.get("year", today.year)),
    })