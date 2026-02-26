# billing/pdf.py
from decimal import Decimal

from django.utils import timezone
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


def _draw_dark_text(p, x, y, text, center=False, right=False):
    """Clean darkness hack with alignment options"""
    if center:
        p.drawCentredString(x, y, text)
        p.drawCentredString(x + 0.15, y, text)
    elif right:
        p.drawRightString(x, y, text)
        p.drawRightString(x + 0.15, y, text)
    else:
        p.drawString(x, y, text)
        p.drawString(x + 0.15, y, text)


def draw_bill_pdf(*, bill, output) -> None:
    items = list(bill.items.select_related("item").all())
    local_dt = timezone.localtime(bill.created_at)

    width = 80 * mm
    height = max(180, 100 + (len(items) * 15)) * mm
    p = canvas.Canvas(output, pagesize=(width, height))

    y = height - 12 * mm
    margin_left = 6 * mm
    margin_right = width - 6 * mm

    # --- HEADER ---
    p.setFont("Courier-Bold", 14)
    _draw_dark_text(p, width / 2, y, "MAHAKAAL THEMES CAFE", center=True)
    y -= 6 * mm
    p.setFont("Courier", 8)
    p.drawCentredString(width / 2, y, "Plot 92, Lakhuja Heights, Bhilwara")
    y -= 4 * mm
    p.drawCentredString(width / 2, y, "GST: 08MAQPS9885M1ZX | 9530301414")
    y -= 6 * mm

    p.setDash(1, 1)  # Dotted line
    p.line(margin_left, y, margin_right, y)
    y -= 6 * mm

    # --- INFO ---

    p.setFont("Courier-Bold", 10)
    # Bill Number ko upar rakhein
    _draw_dark_text(p, margin_left, y, f"BILL: {bill.bill_number}")

    # y ko thoda niche shift karein (6mm) taki Date agali line par aaye
    y -= 6 * mm

    p.setFont("Courier", 9)
    # Date ko ab niche wali line par print karein
    p.drawString(margin_left, y, f"DATE: {local_dt.strftime('%d/%m/%y %I:%M%p')}")

    y -= 5 * mm
    p.drawString(margin_left, y, f"CUST: {str(bill.customer_name or 'Cash'):.20}")
    y -= 6 * mm

    # --- TABLE HEADER ---
    p.setFont("Courier-Bold", 9)
    p.drawString(margin_left, y, "ITEM DESCRIPTION")
    p.drawRightString(margin_right, y, "PRICE")
    y -= 5 * mm
    p.line(margin_left, y, margin_right, y)
    y -= 6 * mm

    # --- ITEMS ---
    subtotal = Decimal("0.00")
    for bi in items:
        line_total = bi.price * bi.quantity
        subtotal += line_total

        # Wrapped Name
        p.setFont("Courier-Bold", 10)
        name_lines = simpleSplit(bi.item.name.upper(), "Courier-Bold", 10, 50 * mm)

        for i, line in enumerate(name_lines):
            _draw_dark_text(p, margin_left, y, line)
            if i == 0:  # Print total on first line
                _draw_dark_text(p, margin_right, y, f"{line_total:>8.2f}", right=True)
            y -= 4.5 * mm

        # Qty Details
        p.setFont("Courier", 9)
        p.drawString(margin_left + 2 * mm, y, f"{bi.quantity} x {bi.price}")
        y -= 6 * mm

    p.line(margin_left, y, margin_right, y)
    y -= 7 * mm

    # --- SUMMARY ---
    def add_row(label, val, bold=False):
        nonlocal y
        p.setFont("Courier-Bold" if bold else "Courier", 10)
        p.drawString(margin_left + 20 * mm, y, label)
        p.drawRightString(margin_right, y, f"{val:>8.2f}")
        y -= 5 * mm

    add_row("Sub-Total:", subtotal)
    if bill.discount_amount > 0:
        add_row("Discount:", -bill.discount_amount)

    gst = (subtotal - bill.discount_amount) * (bill.gst_percentage / 2) / 100
    add_row(f"CGST {bill.gst_percentage/2:g}%:", gst)
    add_row(f"SGST {bill.gst_percentage/2:g}%:", gst)

    y -= 2 * mm
    p.setFont("Courier-Bold", 12)
    _draw_dark_text(p, margin_left + 10 * mm, y, "GRAND TOTAL:")
    _draw_dark_text(
        p,
        margin_right,
        y,
        f"Rs {round(subtotal - bill.discount_amount + (gst*2))}/-",
        right=True,
    )
    y -= 10 * mm

    p.setFont("Courier-Bold", 10)
    _draw_dark_text(p, width / 2, y, "THANK YOU! VISIT AGAIN", center=True)

    p.showPage()
    p.save()


def draw_kitchen_pdf(*, recipe, output) -> None:
    """Ultra-Bold Kitchen Slip"""
    items = list(recipe.items.all())
    local_dt = timezone.localtime(recipe.created_at)
    width, height = 80 * mm, 180 * mm
    p = canvas.Canvas(output, pagesize=(width, height))
    y = height - 12 * mm
    margin = 6 * mm

    # KOT Header (Inverted style look)
    p.setFont("Courier-Bold", 16)
    _draw_dark_text(p, width / 2, y, "KITCHEN SLIP", center=True)
    y -= 7 * mm
    p.setFont("Courier-Bold", 12)
    _draw_dark_text(p, width / 2, y, f"STATION: {recipe.station.upper()}", center=True)
    y -= 6 * mm
    p.setFont("Courier", 10)
    p.drawCentredString(
        width / 2, y, f"ID: {recipe.order_id} | {local_dt.strftime('%I:%M %p')}"
    )
    y -= 5 * mm
    p.line(margin, y, width - margin, y)
    y -= 10 * mm

    # KOT Items
    for item in items:
        # Large QTY and Name side-by-side or stacked
        p.setFont("Courier-Bold", 18)
        _draw_dark_text(p, margin, y, f"{item.quantity} x")

        p.setFont("Courier-Bold", 14)
        name_lines = simpleSplit(item.item_name.upper(), "Courier-Bold", 14, 50 * mm)

        # Start name next to QTY
        for i, line in enumerate(name_lines):
            _draw_dark_text(p, margin + 15 * mm, y, line)
            y -= 6 * mm

        if item.notes:
            p.setFont("Courier-BoldOblique", 11)
            _draw_dark_text(p, margin + 5 * mm, y, f">> {item.notes}")
            y -= 6 * mm

        y -= 4 * mm
        p.setDash(2, 2)
        p.line(margin, y, width - margin, y)
        p.setDash(1, 0)
        y -= 8 * mm

    p.showPage()
    p.save()
