# billing/pdf.py
from decimal import Decimal

from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas

from orders.models import Recipe


def draw_bill_pdf(*, bill, output) -> None:
    width = 80 * mm
    height = 220 * mm

    p = canvas.Canvas(output, pagesize=(width, height))
    y = height - 8 * mm

    def text(line, bold=False, center=False):
        nonlocal y
        p.setFont("Courier-Bold" if bold else "Courier", 8.5 if not bold else 9.5)
        if center:
            p.drawCentredString(width / 2, y, line)
        else:
            p.drawString(5 * mm, y, line)
        y -= 4.5 * mm

    # HEADER
    text("MAHAKAAL THEMES CAFE", bold=True, center=True)
    text("Mo. 9530301414", center=True)
    text("FSSAI: 22226107003714", center=True)
    text("GST No: 08MAQPS9885M1ZX", center=True)
    text("Plot No. 92, Lakhuja Heights", center=True)
    text("Sindhu Nagar, Bhilwara", center=True)
    text("-" * 32)

    text(f"Bill No : {bill.bill_number}")
    text(f"Date    : {bill.created_at.strftime('%d-%m-%Y %I:%M %p')}")
    text(f"Customer: {bill.customer_name}")
    text(f"Mobile  : {bill.customer_phone}")
    text("-" * 32)

    text("ITEM        QTY  RATE   AMT", bold=True)
    text("-" * 32)

    subtotal = Decimal("0.00")

    for bi in bill.items.all():
        line_total = bi.price * bi.quantity
        subtotal += line_total
        name = bi.item.name[:10]
        text(f"{name:<10} {bi.quantity:>3} {bi.price:>6} {line_total:>6}")

    text("-" * 32)

    taxable = subtotal - bill.discount_amount
    gst = (taxable * bill.gst_percentage) / Decimal("100")
    total = taxable + gst

    text(f"Sub Total : {subtotal:.2f}")
    if bill.discount_amount:
        text(f"Discount : {bill.discount_amount:.2f}")

    text(f"GST {bill.gst_percentage}% : {gst:.2f}")
    text("-" * 32)
    text(f"TOTAL : Rs {total:.2f}", bold=True)

    text("Thank you! Visit Again", center=True)

    p.showPage()
    p.save()


def draw_kitchen_pdf(*, recipe: Recipe, output) -> None:
    """
    Generate a thermal kitchen/barista slip.
    - Station-wise
    - No prices
    - Includes notes & priority order
    """

    width = 80 * mm
    height = 200 * mm

    p = canvas.Canvas(output, pagesize=(width, height))
    y = height - 8 * mm

    def text(line: str, *, bold: bool = False, center: bool = False) -> None:
        nonlocal y
        p.setFont("Courier-Bold" if bold else "Courier", 9 if bold else 8)
        if center:
            p.drawCentredString(width / 2, y, line)
        else:
            p.drawString(5 * mm, y, line)
        y -= 4.5 * mm

    # -------- HEADER --------
    text("KITCHEN SLIP", bold=True, center=True)
    text(recipe.station, bold=True, center=True)
    text("-" * 32)

    text(f"Order ID : {recipe.order_id}")
    text(f"Time     : {recipe.created_at.strftime('%d-%m-%Y %I:%M %p')}")
    text("-" * 32)

    # -------- ITEMS --------
    for item in recipe.items.all().order_by("priority"):
        text(f"{item.item_name}", bold=True)
        text(f"Qty : {item.quantity}")

        if item.notes:
            text(f"Note: {item.notes}")

        text("-" * 32)

    # -------- FOOTER --------
    text("PREPARE & SERVE", center=True)

    p.showPage()
    p.save()
