from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDay
from django.shortcuts import render
from django.utils.timezone import localdate

from billing.models import Bill, BillItem
from core.decorators import admin_required


@admin_required
def dashboard_home(request):
    mode = request.GET.get("mode", "day")

    today = localdate()
    bills = Bill.objects.none()
    label = ""

    if mode == "day":
        selected_date = request.GET.get("date")

        if selected_date:
            selected_date = date.fromisoformat(selected_date)
        else:
            selected_date = today

        bills = Bill.objects.filter(created_at__date=selected_date)
        label = selected_date.strftime("%d %b %Y")

    elif mode == "month":
        selected_month = int(request.GET.get("month", today.month))
        selected_year = int(request.GET.get("year", today.year))

        bills = Bill.objects.filter(
            created_at__year=selected_year,
            created_at__month=selected_month,
        )

        label = f"{date(selected_year, selected_month, 1).strftime('%B %Y')}"

    elif mode == "year":
        selected_year = int(request.GET.get("year", today.year))
        bills = Bill.objects.filter(created_at__year=selected_year)
        label = str(selected_year)

    revenue_expr = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    total_bills = bills.count()

    total_sales = Decimal("0.00")
    total_discount = Decimal("0.00")
    total_gst = Decimal("0.00")

    for bill in bills:
        total_sales += bill.total_amount()
        total_discount += bill.discount_amount
        total_gst += bill.gst_amount()

    total_qty = (
        BillItem.objects.filter(bill__in=bills).aggregate(qty=Sum("quantity"))["qty"]
        or 0
    )

    avg_bill = total_sales / total_bills if total_bills > 0 else Decimal("0.00")

    top_items = (
        BillItem.objects.filter(bill__in=bills)
        .values("item__name")
        .annotate(qty=Sum("quantity"), revenue=Sum(revenue_expr))
        .order_by("-qty")
    )

    payment_split = bills.values("payment_mode").annotate(revenue=Sum("items__price"))

    hourly_sales = (
        BillItem.objects.filter(bill__in=bills)
        .annotate(hour=ExtractHour("bill__created_at"))
        .values("hour")
        .annotate(revenue=Sum(revenue_expr))
        .order_by("hour")
    )

    daily_sales = (
        BillItem.objects.filter(bill__in=bills)
        .annotate(day=TruncDay("bill__created_at"))
        .values("day")
        .annotate(revenue=Sum(revenue_expr))
        .order_by("day")
    )

    weekly_sales = (
        BillItem.objects.filter(bill__in=bills)
        .annotate(week=ExtractWeekDay("bill__created_at"))
        .values("week")
        .annotate(revenue=Sum(revenue_expr))
        .order_by("week")
    )

    top_revenue_items = (
        BillItem.objects.filter(bill__in=bills)
        .values("item__name")
        .annotate(revenue=Sum(revenue_expr))
        .order_by("-revenue")[:10]
    )

    busiest_tables = (
        BillItem.objects.filter(bill__in=bills)
        .values("bill__orders__table__number")
        .annotate(total_items=Sum("quantity"))
        .order_by("-total_items")[:10]
    )

    category_sales = (
        BillItem.objects.filter(bill__in=bills)
        .values("item__category__name")
        .annotate(
            revenue=Sum(revenue_expr),
            qty=Sum("quantity"),
        )
        .order_by("-revenue")
    )

    return render(
        request,
        "dashboard/index.html",
        {
            "mode": mode,
            "label": label,
            "total_sales": total_sales,
            "total_bills": total_bills,
            "total_discount": total_discount,
            "total_gst": total_gst,
            "total_qty": total_qty,
            "avg_bill": avg_bill,
            "top_items": top_items,
            "payment_split": payment_split,
            "hourly_sales": hourly_sales,
            "daily_sales": daily_sales,
            "weekly_sales": weekly_sales,
            "top_revenue_items": top_revenue_items,
            "busiest_tables": busiest_tables,
            "category_sales": category_sales,
            "months": range(1, 13),
            "selected_date": request.GET.get("date", today.isoformat()),
            "selected_month": int(request.GET.get("month", today.month)),
            "selected_year": int(request.GET.get("year", today.year)),
        },
    )
