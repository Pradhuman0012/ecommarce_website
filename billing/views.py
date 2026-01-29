import json
from decimal import Decimal
from io import BytesIO

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
            print("ORDER ID:", order.id)
            print("ORDER ITEMS:", order.items.count())
            print("RECIPES COUNT:", order.recipes.count())
            # --------------------
            # 6. PRINT CUSTOMER BILL
            # --------------------
            bill_buffer = BytesIO()

            draw_bill_pdf(
                bill=bill,
                output=bill_buffer,
            )

            save_pdf_once(
                pdf_buffer=bill_buffer,
                filename=f"{bill.bill_number}.pdf",
            )

            bill.bill_pdf_path = f"bills/{bill.bill_number}.pdf"
            bill.save(update_fields=["bill_pdf_path"])

            # --------------------
            # 7. PRINT KITCHEN / BARISTA SLIPS
            # --------------------
            for recipe in order.recipes.all():
                recipe_buffer = BytesIO()

                draw_kitchen_pdf(
                    recipe=recipe,
                    output=recipe_buffer,
                )

                save_pdf_once(
                    pdf_buffer=recipe_buffer,
                    filename=f"order_{order.id}_{recipe.station}.pdf",
                )

            return render(
                request,
                "billing/auto_print.html",
                {
                    "bill": bill,
                    "order": order,
                },
            )

    return render(
        request,
        "billing/create_bill.html",
        {
            "items": items,
            "gst_percentage": float(gst_percentage),
        },
    )


@staff_required
def bill_detail(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    items = bill.items.select_related("item")

    subtotal = sum(i.line_total() for i in items)
    taxable_amount = subtotal - bill.discount_amount
    gst_amount = (taxable_amount * bill.gst_percentage) / Decimal("100")
    total_amount = taxable_amount + gst_amount

    return render(
        request,
        "billing/bill_detail.html",
        {
            "bill": bill,
            "items": items,
            "subtotal": subtotal,
            "gst_amount": gst_amount,
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
