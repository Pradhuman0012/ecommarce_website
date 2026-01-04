from urllib import request
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Bill
from reportlab.lib.pagesizes import mm
import json
from reportlab.pdfgen import canvas
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from decimal import Decimal
import uuid
from .models import Bill, BillItem
from home.models import Item
from orders.models import Order, OrderItem
from orders.service import generate_recipes_for_order
from django.db import transaction
from .models import Bill, BillItem, CafeConfig
from utils.save_pdf import save_pdf_once
from utils.pdf import draw_bill_pdf
from io import BytesIO

def create_bill(request):
    items = Item.objects.prefetch_related("sizes").filter(is_available=True)

    if request.method == "POST":
        with transaction.atomic():
            
            customer_name = request.POST.get("customer_name")
            customer_phone = request.POST.get("customer_phone")
            payment_mode = request.POST.get("payment_mode", "UPI")
            cash_received = request.POST.get("cash_received")
            change_amount = request.POST.get("change_amount")
            discount_percent = Decimal(request.POST.get("discount_percent") or 0)

            cafe = CafeConfig.objects.first()
            gst_percentage = cafe.gst_percentage if cafe else Decimal("0")

            bill_number = f"BILL-{uuid.uuid4().hex[:8].upper()}"
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

                item = Item.objects.get(id=int(data["item_id"]))
                price = Decimal(str(data["price"]))
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
                (subtotal * discount_percent) / Decimal("100"),
                subtotal
            )
            bill.discount_amount = discount_amount
            bill.save()

            # --------------------
            # 5. GENERATE RECIPES
            # --------------------
            generate_recipes_for_order(order)

            
            buffer = BytesIO()
            draw_bill_pdf(bill=bill, output=buffer)
            print("PDF size:", buffer.getbuffer().nbytes)
            save_pdf_once(
                pdf_buffer=buffer,
                filename=f"{bill.bill_number}.pdf",
            )
            return render(request, "billing/auto_print.html", {
                "bill": bill,
                "order": order,
            })
                        
    return render(request, "billing/create_bill.html", {"items": items})

def bill_detail(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    items = bill.items.select_related("item")

    subtotal = sum(i.line_total() for i in items)
    taxable_amount = subtotal - bill.discount_amount
    gst_amount = (taxable_amount * bill.gst_percentage) / Decimal("100")
    total_amount = taxable_amount + gst_amount

    return render(request, "billing/bill_detail.html", {
        "bill": bill,
        "items": items,
        "subtotal": subtotal,
        "gst_amount": gst_amount,
        "total_amount": total_amount,
    })


def bill_pdf(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{bill.bill_number}.pdf"'

    draw_bill_pdf(bill=bill, output=response)
    return response
    bill = get_object_or_404(Bill, id=bill_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{bill.bill_number}.pdf"'

    # 80mm thermal size
    width = 80 * mm
    height = 220 * mm

    p = canvas.Canvas(response, pagesize=(width, height))
    y = height - 8 * mm

    def text(line, bold=False, center=False):
        nonlocal y
        p.setFont("Courier-Bold" if bold else "Courier", 8.5 if not bold else 9.5)
        if center:
            p.drawCentredString(width / 2, y, line)
        else:
            p.drawString(5 * mm, y, line)
        y -= 4.5 * mm

    # ---------- HEADER ----------
    text("MAHAKAAL THEMES CAFE", bold=True, center=True)
    text("Mo. 9530303016", center=True)
    text("GST No: 08MAQPS9885M1ZX", center=True)
    text("Plot No. 92, Lakhuja Heights", center=True)
    text("Sindhu Nagar, Bhilwara", center=True)
    text("-" * 32)

    # ---------- BILL INFO ----------
    text(f"Bill No : {bill.bill_number}")
    text(f"Date    : {bill.created_at.strftime('%d-%m-%Y %I:%M %p')}")
    text(f"Customer: {bill.customer_name}")
    text(f"Mobile  : {bill.customer_phone}")
    text("-" * 32)

    # ---------- TABLE HEADER ----------
    text("ITEM        QTY  RATE   AMT", bold=True)
    text("-" * 32)

    # ---------- ITEMS ----------
    subtotal = Decimal("0.00")

    for bi in bill.items.all():
        line_total = bi.price * bi.quantity
        subtotal += line_total

        name = bi.item.name[:10]  # trim for thermal width
        text(f"{name:<10} {bi.quantity:>3} {bi.price:>6} {line_total:>6}")

    # ---------- TOTALS ----------
    text("-" * 32)

    taxable_amount = max(subtotal - bill.discount_amount, Decimal("0.00"))
    gst_total = (taxable_amount * bill.gst_percentage) / Decimal("100")
    cgst = gst_total / 2
    sgst = gst_total / 2
    grand_total = taxable_amount + gst_total

    text(f"Sub Total     : {subtotal:>7.2f}")

    if bill.discount_amount > 0:
        text(
            f"Discount ({bill.discount_percent:.0f}%)"
            f" : {bill.discount_amount:>7.2f}"
        )

    text(f"CGST @{bill.gst_percentage/2:.2f}% : {cgst:>7.2f}")
    text(f"SGST @{bill.gst_percentage/2:.2f}% : {sgst:>7.2f}")

    text("-" * 32)
    text(f"TOTAL         : ₹ {grand_total:.2f}", bold=True)
    # ---------- FOOTER ----------
    y -= 3 * mm
    text("Thank you! Visit Again", center=True)
    text("Powered by MTC", center=True)

    p.showPage()
    p.save()
    return response