from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from billing.models import Bill, BillItem
from core.decorators import admin_required

from .models import CashTransaction, Customer, DailyCashCounter, Expense, Staff


# ═══════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════
@admin_required
def admin_dashboard(request):
    date_str = request.GET.get("date")
    if date_str:
        try:
            today = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            today = timezone.localdate()
    else:
        today = timezone.localdate()

    yesterday = today - timedelta(days=1)
    first_of_month = today.replace(day=1)

    # ── Today's Sales ──
    today_bills = Bill.objects.filter(created_at__date=today)
    today_revenue = sum(b.total_amount() for b in today_bills)
    today_bill_count = today_bills.count()
    # Cash = full amount for CASH bills + cash_received portion for SPLIT bills
    today_cash = sum(b.total_amount() for b in today_bills.filter(payment_mode="CASH"))
    today_cash += sum(
        (b.cash_received or 0) for b in today_bills.filter(payment_mode="SPLIT")
    )
    today_upi = sum(b.total_amount() for b in today_bills.filter(payment_mode="UPI"))

    # ── Yesterday's Sales (for comparison) ──
    yest_bills = Bill.objects.filter(created_at__date=yesterday)
    yest_revenue = sum(b.total_amount() for b in yest_bills)
    yest_bill_count = yest_bills.count()

    # ── Monthly ──
    monthly_bills = Bill.objects.filter(created_at__date__gte=first_of_month)
    monthly_revenue = sum(b.total_amount() for b in monthly_bills)
    monthly_bill_count = monthly_bills.count()

    monthly_expenses = Expense.objects.filter(date__gte=first_of_month).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    total_salary = Staff.objects.filter(is_active=True).aggregate(total=Sum("salary"))[
        "total"
    ] or Decimal("0")
    active_staff = Staff.objects.filter(is_active=True).count()
    net = monthly_revenue - monthly_expenses - total_salary

    # ── Last 7 days revenue ──
    last7_start = today - timedelta(days=6)
    daily_data = []
    for i in range(7):
        d = last7_start + timedelta(days=i)
        day_bills = Bill.objects.filter(created_at__date=d)
        day_rev = sum(b.total_amount() for b in day_bills)
        daily_data.append({"day": d, "revenue": float(day_rev)})

    # ── Top 5 selling items today ──
    top_items = (
        BillItem.objects.filter(bill__created_at__date=today)
        .values("item__name")
        .annotate(qty=Sum("quantity"))
        .order_by("-qty")[:5]
    )

    # ── Expense category breakdown (this month) ──
    cat_data = (
        Expense.objects.filter(date__gte=first_of_month)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    # ── Cash Counter ──
    counter = DailyCashCounter.objects.filter(date=today).first()
    opening = counter.opening_balance if counter else Decimal("0")
    cash_out = Decimal("0")
    if counter:
        cash_out = counter.transactions.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
    expected_cash = opening + today_cash - cash_out

    # ── Recent expenses ──
    recent_expenses = Expense.objects.all().order_by("-date", "-created_at")[:5]

    return render(
        request,
        "administration/dashboard.html",
        {
            "today": today,
            "date_input": today.strftime("%Y-%m-%d"),
            # Today
            "today_revenue": today_revenue,
            "today_bill_count": today_bill_count,
            "today_cash": today_cash,
            "today_upi": today_upi,
            # Yesterday comparison
            "yest_revenue": yest_revenue,
            "yest_bill_count": yest_bill_count,
            # Monthly
            "monthly_revenue": monthly_revenue,
            "monthly_bill_count": monthly_bill_count,
            "monthly_expenses": monthly_expenses,
            "total_salary": total_salary,
            "active_staff": active_staff,
            "net": net,
            # Charts
            "daily_data": daily_data,
            "top_items": top_items,
            "cat_data": cat_data,
            # Cash
            "expected_cash": expected_cash,
            # Recent
            "recent_expenses": recent_expenses,
        },
    )


# ═══════════════════════════════════════════════════
#  CASH COUNTER
# ═══════════════════════════════════════════════════
@admin_required
def cash_counter_view(request):
    today = timezone.localdate()
    counter, _ = DailyCashCounter.objects.get_or_create(date=today)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "set_opening":
            counter.opening_balance = Decimal(request.POST.get("opening_balance") or 0)
            counter.notes = request.POST.get("notes", "")
            counter.save()

        elif action == "add_cash_in":
            amount = Decimal(request.POST.get("amount") or 0)
            reason = request.POST.get("reason", "")
            if amount > 0:
                CashTransaction.objects.create(
                    daily_counter=counter,
                    amount=amount,
                    reason=reason,
                    tx_type=CashTransaction.TransactionType.IN,
                )

        elif action == "add_withdrawal":
            amount = Decimal(request.POST.get("amount") or 0)
            reason = request.POST.get("reason", "")
            if amount > 0:
                CashTransaction.objects.create(
                    daily_counter=counter,
                    amount=amount,
                    reason=reason,
                    tx_type=CashTransaction.TransactionType.OUT,
                )

        elif action == "delete_withdrawal":
            txn_id = request.POST.get("txn_id")
            CashTransaction.objects.filter(id=txn_id, daily_counter=counter).delete()

        return redirect("administration:cash_counter")

    # ── Calculations ──
    today_cash_bills = sum(
        bill.total_amount()
        for bill in Bill.objects.filter(created_at__date=today, payment_mode="CASH")
    )

    # Add cash portion from SPLIT bills
    today_cash_bills += sum(
        (bill.cash_received or Decimal("0"))
        for bill in Bill.objects.filter(created_at__date=today, payment_mode="SPLIT")
    )

    withdrawals = counter.transactions.filter(
        tx_type=CashTransaction.TransactionType.OUT
    )
    total_withdrawn = withdrawals.aggregate(total=Sum("amount"))["total"] or Decimal(
        "0"
    )

    manual_in = counter.transactions.filter(tx_type=CashTransaction.TransactionType.IN)
    total_manual_in = manual_in.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    today_cash_in = today_cash_bills + total_manual_in
    expected_cash = counter.opening_balance + today_cash_in - total_withdrawn

    # Today's all bills for display
    today_bills = Bill.objects.filter(created_at__date=today).order_by("-created_at")

    return render(
        request,
        "administration/cash_counter.html",
        {
            "counter": counter,
            "today_cash_bills": today_cash_bills,
            "total_manual_in": total_manual_in,
            "all_transactions": counter.transactions.all(),
            "total_withdrawn": total_withdrawn,
            "expected_cash": expected_cash,
            "today_bills": today_bills,
        },
    )


# ═══════════════════════════════════════════════════
#  STAFF
# ═══════════════════════════════════════════════════
@admin_required
def staff_list_view(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            staff = Staff(
                name=request.POST.get("name", ""),
                role=request.POST.get("role", ""),
                phone=request.POST.get("phone", ""),
                salary=Decimal(request.POST.get("salary") or 0),
                aadhar_number=request.POST.get("aadhar_number", ""),
            )
            if request.FILES.get("photo"):
                staff.photo = request.FILES["photo"]
            staff.save()

        elif action == "edit":
            staff = get_object_or_404(Staff, id=request.POST.get("staff_id"))
            staff.name = request.POST.get("name", staff.name)
            staff.role = request.POST.get("role", staff.role)
            staff.phone = request.POST.get("phone", staff.phone)
            staff.salary = Decimal(request.POST.get("salary") or staff.salary)
            staff.aadhar_number = request.POST.get("aadhar_number", staff.aadhar_number)
            if request.FILES.get("photo"):
                staff.photo = request.FILES["photo"]
            staff.save()

        elif action == "toggle":
            staff = get_object_or_404(Staff, id=request.POST.get("staff_id"))
            staff.is_active = not staff.is_active
            staff.save()

        return redirect("administration:staff_list")

    staff_members = Staff.objects.all()
    total_salary = staff_members.filter(is_active=True).aggregate(total=Sum("salary"))[
        "total"
    ] or Decimal("0")

    return render(
        request,
        "administration/staff_list.html",
        {
            "staff_members": staff_members,
            "total_salary": total_salary,
        },
    )


@admin_required
def staff_detail_view(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    return render(
        request,
        "administration/staff_detail.html",
        {
            "staff": staff,
        },
    )


# ═══════════════════════════════════════════════════
#  EXPENSES
# ═══════════════════════════════════════════════════
@admin_required
def expense_list_view(request):
    today = timezone.localdate()
    first_of_month = today.replace(day=1)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            Expense.objects.create(
                date=request.POST.get("date") or today,
                category=request.POST.get("category", "MISC"),
                amount=Decimal(request.POST.get("amount") or 0),
                description=request.POST.get("description", ""),
            )

        elif action == "delete":
            Expense.objects.filter(id=request.POST.get("expense_id")).delete()

        return redirect("administration:expense_list")

    cat_filter = request.GET.get("category", "")
    expenses = Expense.objects.filter(date__gte=first_of_month).order_by(
        "-date", "-created_at"
    )
    if cat_filter:
        expenses = expenses.filter(category=cat_filter)

    monthly_total = expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    return render(
        request,
        "administration/expense_list.html",
        {
            "expenses": expenses,
            "monthly_total": monthly_total,
            "categories": Expense.Category.choices,
            "selected_category": cat_filter,
        },
    )


# ═══════════════════════════════════════════════════
#  CUSTOMERS
# ═══════════════════════════════════════════════════
@admin_required
def customer_list_view(request):
    q = request.GET.get("q", "")
    customers = Customer.objects.all()

    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    # Update total_spent from bills for all visible customers
    for c in customers:
        c.computed_spent = sum(b.total_amount() for b in c.bills.all())

    return render(
        request,
        "administration/customer_list.html",
        {"customers": customers, "query": q},
    )


@admin_required
def customer_detail_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == "POST" and request.POST.get("action") == "update_notes":
        customer.notes = request.POST.get("notes", "")
        customer.save()
        return redirect("administration:customer_detail", customer_id=customer.id)

    bills = customer.bills.all().order_by("-created_at")
    total_spent = sum(b.total_amount() for b in bills)

    return render(
        request,
        "administration/customer_detail.html",
        {
            "customer": customer,
            "bills": bills,
            "total_spent": total_spent,
        },
    )


@admin_required
def get_customer_by_phone(request):
    phone = request.GET.get("phone", "").strip()
    if not phone:
        return JsonResponse(
            {"status": "error", "message": "Phone required"}, status=400
        )

    customer = Customer.objects.filter(phone=phone).first()
    if customer:
        return JsonResponse(
            {
                "status": "success",
                "name": customer.name,
                "visits": customer.total_visits,
            }
        )
    return JsonResponse({"status": "not_found"}, status=404)


@admin_required
def search_customers(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"status": "success", "customers": []})

    customers = Customer.objects.filter(Q(name__icontains=q) | Q(phone__icontains=q))[
        :10
    ]  # Limit to 10 results for performance

    results = []
    for c in customers:
        results.append(
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
            }
        )

    return JsonResponse({"status": "success", "customers": results})
