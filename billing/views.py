import json
import os
from decimal import Decimal
from io import BytesIO

import win32api
import win32print
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse

# Create your views here.
from django.shortcuts import get_object_or_404, render

from core.decorators import staff_required
from home.models import Item
from orders.models import Order, OrderItem
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
            generate_recipes_for_order(order)

            # --------------------
            # 6. PRINT CUSTOMER BILL
            # --------------------
            bill_buffer = BytesIO()

            draw_bill_pdf(
                bill=bill,
                output=bill_buffer,
            )

            bill_filename = f"{bill.bill_number}.pdf"

            save_pdf_once(
                pdf_buffer=bill_buffer,
                filename=bill_filename,
            )

            bill_relative_path = f"bills/{bill_filename}"

            bill.bill_pdf_path = bill_relative_path
            bill.save(update_fields=["bill_pdf_path"])

            # 🧾 SEND TO USB PRINTER
            send_to_printer(
                file_relative_path=bill_relative_path, printer_name="POS-80C USB"
            )

            # --------------------
            # 7. PRINT KITCHEN SLIPS
            # --------------------
            for recipe in order.recipes.all():

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

                # 🍳 Send to BT printer
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

    subtotal = sum(i.line_total() for i in items)
    taxable_amount = subtotal - bill.discount_amount
    gst_amount = (taxable_amount * bill.gst_percentage) / Decimal("100")
    gst_split_rate = bill.gst_percentage / Decimal("2")
    cgst_amount = (taxable_amount * gst_split_rate) / Decimal("100")
    sgst_amount = (taxable_amount * gst_split_rate) / Decimal("100")
    total_amount = taxable_amount + gst_amount

    return render(
        request,
        "billing/bill_detail.html",
        {
            "bill": bill,
            "items": items,
            "subtotal": subtotal,
            "cgst_amount": cgst_amount,
            "sgst_amount": sgst_amount,
            "total_amount": total_amount,
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
    # Order ko find karein
    order = get_object_or_404(Order, id=order_id)

    # Ek order mein kai recipes (stations) ho sakti hain
    # Hum saari recipes ko ek hi PDF mein ya alag-alag dikha sakte hain.
    # Filhal ye view pehli available recipe generate karega:
    recipe = order.recipes.first()

    if not recipe:
        return HttpResponse("No kitchen slip available for this order.", status=404)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="KOT_{order.id}.pdf"'

    # Aapka draw_kitchen_pdf function call karein
    draw_kitchen_pdf(recipe=recipe, output=response)
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
