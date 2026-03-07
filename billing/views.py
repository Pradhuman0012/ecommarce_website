import json
import os
from decimal import Decimal
from io import BytesIO

import win32api
import win32print
from django.conf import settings
from django.db import transaction
from django.db.models import IntegerField
from django.db.models.functions import Cast, Substr
from django.http import HttpResponse, JsonResponse

# Create your views here.
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import staff_required
from home.models import Category, Item
from orders.models import Order, OrderHistory, OrderItem, Table
from orders.service import generate_recipes_for_order
from utils.pdf import draw_bill_pdf, draw_kitchen_pdf
from utils.save_pdf import save_pdf_once

from .models import Bill, BillItem, CafeConfig


@staff_required
def create_bill(request):
    items = Item.objects.prefetch_related("sizes").filter(is_available=True)
    cafe = CafeConfig.objects.first()
    gst_percentage = cafe.gst_percentage if cafe else Decimal("0")
    cgst_percentage = gst_percentage / Decimal("2")
    sgst_percentage = gst_percentage / Decimal("2")

    if request.method == "POST":
        with transaction.atomic():

            customer_name = request.POST.get("customer_name")
            customer_phone = request.POST.get("customer_phone")
            payment_mode = request.POST.get("payment_mode", "UPI")
            cash_received = request.POST.get("cash_received")
            change_amount = request.POST.get("change_amount")
            discount_percent = Decimal(request.POST.get("discount_percent") or 0)

            items_data = json.loads(request.POST.get("items_payload") or "{}")

            subtotal = Decimal("0.00")

            # --------------------
            # 1. CREATE BILL
            # --------------------
            bill = Bill.objects.create(
                customer_name=customer_name,
                customer_phone=customer_phone,
                payment_mode=payment_mode,
                cash_received=Decimal(cash_received) if cash_received else None,
                change_returned=Decimal(change_amount) if change_amount else None,
                discount_amount=Decimal("0.00"),
                discount_percent=discount_percent,
                gst_percentage=gst_percentage,
            )

            # --------------------
            # 2. CREATE ORDER (NEW)
            # --------------------
            order = Order.objects.create(
                bill=bill,
                customer_name=customer_name,
            )

            # --------------------
            # 3. ADD ITEMS
            # --------------------
            order_items = []

            for data in items_data.values():
                qty = int(data["qty"])
                if qty <= 0:
                    continue

                item = Item.objects.select_related().get(id=int(data["item_id"]))
                price = item.get_price_for_size(data["size"])
                priority = int(data.get("priority", 1))
                notes = data.get("notes", "")

                line_total = price * qty
                subtotal += line_total

                # BILL ITEM
                BillItem.objects.create(
                    bill=bill,
                    item=item,
                    size=data["size"],
                    price=price,
                    quantity=qty,
                )

                # ORDER ITEM
                order_items.append(
                    OrderItem(
                        order=order,
                        item=item,
                        quantity=qty,
                        priority=priority,
                        notes=notes,
                    )
                )

            OrderItem.objects.bulk_create(order_items)

            # --------------------
            # 4. APPLY DISCOUNT
            # --------------------
            discount_amount = min(
                (subtotal * discount_percent) / Decimal("100"), subtotal
            )
            bill.discount_amount = discount_amount
            bill.save()

            # --------------------
            # 5. GENERATE RECIPES
            # --------------------
            unsent_items = order.items.filter(is_sent_to_kitchen=False)

            recipes = generate_recipes_for_order(order, items=unsent_items)

            unsent_items.update(is_sent_to_kitchen=True)

            # --------------------
            # 7. PRINT KITCHEN SLIPS
            # --------------------
            for recipe in recipes:

                recipe_buffer = BytesIO()

                draw_kitchen_pdf(
                    recipe=recipe,
                    output=recipe_buffer,
                )

                recipe_filename = f"order_{order.id}_{recipe.station}.pdf"

                save_pdf_once(
                    pdf_buffer=recipe_buffer,
                    filename=recipe_filename,
                )

                recipe_relative_path = f"bills/{recipe_filename}"

                send_to_printer(
                    file_relative_path=recipe_relative_path, printer_name="POS-80C BT"
                )

    return render(
        request,
        "billing/create_bill.html",
        {
            "items": items,
            "cgst_percentage": cgst_percentage,
            "sgst_percentage": sgst_percentage,
        },
    )


@staff_required
def bill_detail(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    items = bill.items.select_related("item")

    # 1. Basic Calculations
    subtotal = sum(i.line_total() for i in items)
    taxable_amount = subtotal - bill.discount_amount

    # 2. GST Calculations (2.5% each if total is 5%)
    # Agar bill.gst_percentage 5 hai, toh split_rate 2.5 hoga
    gst_split_rate = bill.gst_percentage / Decimal("2")
    cgst_amount = (taxable_amount * gst_split_rate) / Decimal("100")
    sgst_amount = (taxable_amount * gst_split_rate) / Decimal("100")

    # 3. Total before rounding
    total_before_round = taxable_amount + cgst_amount + sgst_amount

    # 4. Final Rounding Logic
    # Decimal ko float mein convert karke round karenge phir wapas Decimal
    final_total = Decimal(round(float(total_before_round)))

    # Difference nikal rahe hain (e.g. +0.25 ya -0.40)
    round_off_val = final_total - total_before_round

    return render(
        request,
        "billing/bill_detail.html",
        {
            "bill": bill,
            "items": items,
            "subtotal": subtotal,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "total_amount": final_total,  # Rounded figure
            "round_off": round_off_val,  # Difference for UI
        },
    )


@staff_required
def bill_pdf(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{bill.bill_number}.pdf"'

    draw_bill_pdf(bill=bill, output=response)
    return response


@staff_required
def kitchen_pdf(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "recipes__items",
            "recipes__order__table",
        ),
        id=order_id,
    )

    recipes = order.recipes.all()

    if not recipes.exists():
        return HttpResponse("No kitchen slip available", status=404)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="KOT_{order.id}.pdf"'

    for recipe in recipes:
        draw_kitchen_pdf(
            recipe=recipe,
            output=response,
        )

    return response


def send_to_printer(file_relative_path, printer_name):
    file_path = os.path.join(settings.MEDIA_ROOT, file_relative_path)

    if not os.path.exists(file_path):
        print("File not found:", file_path)
        return

    # Set printer
    handle = win32print.OpenPrinter(printer_name)

    try:
        win32api.ShellExecute(0, "printto", file_path, f'"{printer_name}"', ".", 0)
    finally:
        win32print.ClosePrinter(handle)


@staff_required
def table_order_view(request):
    tables = Table.objects.annotate(
        num=Cast(Substr("number", 2), IntegerField())
    ).order_by("num")

    items = Item.objects.filter(is_available=True)
    categories = Category.objects.all()

    if request.method == "POST":
        table_id = request.POST.get("table_id")
        action_type = request.POST.get("action_type")
        items_data = json.loads(request.POST.get("items_payload") or "{}")
        table = get_object_or_404(Table, id=table_id)

        with transaction.atomic():
            # --- CASE 1: SEND KOT ---
            if action_type == "KOT":

                if not items_data:
                    return JsonResponse({"error": "No items to send"}, status=400)

                # reuse open order
                order = (
                    Order.objects.filter(table=table, is_billed=False)
                    .order_by("-created_at")
                    .first()
                )

                if not order:
                    order = Order.objects.create(
                        table=table,
                        customer_name=f"Table {table.number}",
                        status=Order.Status.NEW,
                    )

                created_items = []

                for data in items_data.values():

                    item = Item.objects.get(id=int(data["id"]))

                    oi = OrderItem.objects.create(
                        order=order,
                        item=item,
                        quantity=int(data["qty"]),
                        size=data["size"],
                        notes=data.get("notes", ""),
                        is_sent_to_kitchen=False,
                    )

                    created_items.append(oi)

                # create recipes
                unsent_items = order.items.filter(is_sent_to_kitchen=False)

                if unsent_items.exists():

                    recipes = generate_recipes_for_order(order, items=unsent_items)

                    for recipe in recipes:

                        recipe_buffer = BytesIO()

                        draw_kitchen_pdf(recipe=recipe, output=recipe_buffer)

                        recipe_filename = f"KOT_{order.id}_{recipe.station}.pdf"

                        save_pdf_once(
                            pdf_buffer=recipe_buffer,
                            filename=recipe_filename,
                        )

                        recipe_relative_path = f"bills/{recipe_filename}"

                        send_to_printer(
                            file_relative_path=recipe_relative_path,
                            printer_name="POS-80C BT",
                        )

                    unsent_items.update(is_sent_to_kitchen=True)

                table.is_occupied = True
                table.save()

                return redirect("billing:table_order")
            # --- CASE 2: FINAL BILL (Fixed Logic) ---
            elif action_type == "BILL":
                pending_orders = table.orders.filter(is_billed=False)

                # Frontend se values uthayein
                discount_percent = Decimal(
                    request.POST.get("discount_pct") or 0
                )  # HTML name fDiscountPct check karein
                payment_mode = request.POST.get("payment_mode", "UPI")
                cust_name = request.POST.get("customer_name") or f"Table {table.number}"
                cust_phone = request.POST.get("customer_phone")

                cafe = CafeConfig.objects.first()
                bill = Bill.objects.create(
                    customer_name=cust_name,
                    customer_phone=cust_phone,
                    payment_mode=payment_mode,
                    gst_percentage=cafe.gst_percentage if cafe else 0,
                    discount_percent=discount_percent,
                )

                subtotal = Decimal("0.00")

                # Step A: Purane (Already served) items add karein
                for order in pending_orders:

                    items_snapshot = []

                    for ot in order.items.select_related("item"):

                        price = ot.item.get_price_for_size(ot.size)
                        subtotal += price * ot.quantity

                        BillItem.objects.create(
                            bill=bill,
                            item=ot.item,
                            size=ot.size,
                            quantity=ot.quantity,
                            price=price,
                        )

                        items_snapshot.append(
                            {
                                "item_name": ot.item.name,
                                "quantity": ot.quantity,
                                "size": ot.size,
                                "price": str(price),
                                "notes": ot.notes,
                                "priority": ot.priority,
                            }
                        )

                    order.bill = bill
                    order.is_billed = True
                    order.save()

                    OrderHistory.objects.create(
                        order=order,
                        bill_number=bill.bill_number,
                        customer_name=bill.customer_name,
                        customer_phone=bill.customer_phone,
                        payment_mode=bill.payment_mode,
                        subtotal=0,  # will override in view
                        discount=bill.discount_amount,
                        gst=0,
                        total_amount=0,
                        cash_received=bill.cash_received,
                        change_returned=bill.change_returned,
                        bill_pdf_path=bill.bill_pdf_path or "",
                        items_snapshot=items_snapshot,
                    )

                # Step B: Naye items (Screen se direct bill)
                for key, data in items_data.items():
                    item = Item.objects.get(id=int(data["id"]))
                    price = item.get_price_for_size(data["size"])
                    qty = int(data["qty"])
                    subtotal += price * qty
                    BillItem.objects.create(
                        bill=bill,
                        item=item,
                        size=data["size"],
                        quantity=qty,
                        price=price,
                    )

                # Step C: Discount & Final Save
                discount_amount = (subtotal * discount_percent) / Decimal("100")
                bill.discount_amount = discount_amount
                bill.save()

                # Bill PDF Generation (Existing logic)
                bill_buffer = BytesIO()
                draw_bill_pdf(bill=bill, output=bill_buffer)
                bill_filename = f"BILL_{bill.bill_number}.pdf"
                save_pdf_once(pdf_buffer=bill_buffer, filename=bill_filename)
                bill.bill_pdf_path = f"bills/{bill_filename}"
                send_to_printer(
                    file_relative_path=bill.bill_pdf_path, printer_name="POS-80C USB"
                )
                bill.save()

                table.is_occupied = False
                table.save()
                return redirect("billing:table_order")

    return render(
        request,
        "billing/table_order.html",
        {"categories": categories, "items": items, "tables": tables},
    )


@staff_required
def get_table_order(request, table_id):
    """Specific table ke saare active items fetch karne ke liye"""
    table = get_object_or_404(Table, id=table_id)
    # Saare orders uthao jo abhi tak bill nahi hue hain
    active_orders = Order.objects.filter(table=table, is_billed=False).prefetch_related(
        "items__item"
    )

    data = []
    for order in active_orders:
        for oi in order.items.all():
            data.append(
                {
                    "name": oi.item.name,
                    "qty": oi.quantity,
                    "size": oi.size,
                    "price": float(oi.item.get_price_for_size(oi.size)),
                    "notes": oi.notes,
                }
            )

    return JsonResponse({"items": data})
