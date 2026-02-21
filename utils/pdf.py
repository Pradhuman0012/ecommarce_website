# billing/pdf.py
from decimal import Decimal

from django.utils import timezone
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from orders.models import Recipe


def _draw_dark_text(
    p: canvas.Canvas,
    x: float,
    y: float,
    text: str,
    *,
    center: bool = False,
) -> None:
    """
    Draw darker text by overlapping the same text twice.
    This significantly improves thermal printer darkness.
    """
    if center:
        p.drawCentredString(x, y, text)
        p.drawCentredString(x + 0.35, y, text)
    else:
        p.drawString(x, y, text)
        p.drawString(x + 0.35, y, text)


def draw_bill_pdf(*, bill, output) -> None:
    width = 80 * mm
    # Paper height dynamic ho sakti hai, 200mm is fine.
    height = 200 * mm

    p = canvas.Canvas(output, pagesize=(width, height))
    y = height - 10 * mm
    margin = 4 * mm
    # 80mm width aur Courier 10.5 font ke liye approx 32-34 chars aate hain
    line_width = 32

    def text(line: str, *, bold: bool = False, center: bool = False, spacing=5) -> None:
        nonlocal y
        # Font size thoda chota kiya taaki wrap kam ho aur clear dikhe
        p.setFont("Courier-Bold", 10 if not bold else 11)
        x = width / 2 if center else margin
        _draw_dark_text(p, x, y, line, center=center)
        y -= spacing * mm

    # -------- HEADER --------
    text("MAHAKAAL THEMES CAFE", bold=True, center=True)
    text("Mo. 9530301414", center=True, spacing=4)
    text("FSSAI: 22226107003714", center=True, spacing=4)
    text("GST No: 08MAQPS9885M1ZX", center=True, spacing=4)
    text("Plot No. 92, Lakhuja Heights", center=True, spacing=4)
    text("Sindhu Nagar, Bhilwara", center=True, spacing=4)
    text("-" * line_width)
    local_dt = timezone.localtime(bill.created_at)

    text(f"Bill No : {bill.bill_number}")
    text(f"Date    : {local_dt.strftime('%d/%m/%y %I:%M %p')}")
    text(f"Cust.   : {bill.customer_name[:20]}")  # Truncate long names to avoid mess
    text(f"Mobile  : {bill.customer_phone}")
    text("-" * line_width)

    # Columns Header: fixed width approach
    # ITEM (14) + QTY (4) + RATE (6) + AMT (7) = 31 chars
    text("ITEM          QTY  RATE   AMT", bold=True)
    text("-" * line_width)

    subtotal = Decimal("0.00")

    for bi in bill.items.all():
        line_total = bi.price * bi.quantity
        subtotal += line_total

        full_name = bi.item.name
        # Item name width 40mm tak limited (approx 14-15 chars)
        wrapped_name = simpleSplit(full_name, "Courier-Bold", 10, 38 * mm)

        # First line with values
        item_part = wrapped_name[0].ljust(14)
        text(
            f"{item_part} {bi.quantity:>3} {bi.price:>5.0f} {line_total:>6.0f}",
            spacing=0,
        )
        y -= 4 * mm  # Gap between items

        # Next lines of name if any
        if len(wrapped_name) > 1:
            for extra_line in wrapped_name[1:]:
                text(extra_line, spacing=4)

        y -= 1 * mm  # Small padding between different items

    text("-" * line_width)

    # -------- CALCULATIONS --------
    taxable = subtotal - bill.discount_amount
    half_gst_rate = bill.gst_percentage / Decimal("2")
    cgst_amount = (taxable * half_gst_rate) / Decimal("100")
    sgst_amount = (taxable * half_gst_rate) / Decimal("100")

    exact_total = taxable + cgst_amount + sgst_amount
    rounded_total = round(exact_total)
    round_off_diff = rounded_total - exact_total

    # Labels 15 chars + values 12 chars = 27 chars
    text(f"Sub Total      : {subtotal:>10.2f}")
    if bill.discount_amount > 0:
        text(f"Discount       : -{bill.discount_amount:>9.2f}")

    text(f"CGST ({half_gst_rate:g}%)    : {cgst_amount:>10.2f}")
    text(f"SGST ({half_gst_rate:g}%)    : {sgst_amount:>10.2f}")

    if round_off_diff != 0:
        text(f"Round Off      : {round_off_diff:>10.2f}")

    text("-" * line_width)
    # Grand Total bada dikhna chahiye
    p.setFont("Courier-Bold", 12)
    _draw_dark_text(p, margin, y, f"GRAND TOTAL   : Rs {rounded_total:>6.0f}/-")
    y -= 7 * mm
    p.setFont("Courier-Bold", 10)
    text("-" * line_width)

    text("Thank you! Visit Again", bold=True, center=True)

    p.showPage()
    p.save()


def draw_kitchen_pdf(*, recipe: Recipe, output) -> None:
    """
    KOT (Kitchen Order Ticket) with Word Wrap.
    Koi bhi item name ya note katega nahi.
    """
    width = 80 * mm
    # KOT lambi ho sakti hai agar items zyada hon, isliye height 170-200mm thik hai
    height = 180 * mm
    local_dt = timezone.localtime(recipe.created_at)

    p = canvas.Canvas(output, pagesize=(width, height))
    y = height - 8 * mm
    margin = 5 * mm
    max_text_width = 70 * mm  # Thermal paper ki usable width

    def text(line: str, *, bold: bool = False, center: bool = False, spacing=5) -> None:
        nonlocal y
        # KOT ke liye font thoda bada rakhte hain taaki kitchen mein door se dikhe
        p.setFont("Courier-Bold", 10.5 if not bold else 12)
        x = width / 2 if center else margin
        _draw_dark_text(p, x, y, line, center=center)
        y -= spacing * mm

    # -------- HEADER --------
    text("KITCHEN SLIP", bold=True, center=True)
    text(f"STATION: {recipe.station.upper()}", bold=True, center=True)
    text("-" * 32)

    text(f"Order ID : {recipe.order_id}")
    text(f"Time     : {local_dt.strftime('%d-%m-%Y %I:%M %p')}")
    text("-" * 32)

    # -------- ITEMS --------
    for item in recipe.items.all().order_by("priority"):
        # 1. Wrap Item Name
        # Agar item name bada hai, toh simpleSplit use agli line mein le jayega
        name_lines = simpleSplit(item.item_name, "Courier-Bold", 12, max_text_width)
        for line in name_lines:
            text(line, bold=True, spacing=5)

        # 2. Quantity (Bade font mein taaki nazar pade)
        text(f"QTY: {item.quantity}", bold=True, spacing=5)

        # 3. Wrap Notes
        if item.notes:
            # Notes ke liye font thoda chota (10) aur wrap logic
            note_lines = simpleSplit(
                f"Note: {item.notes}", "Courier-Bold", 10, max_text_width
            )
            for n_line in note_lines:
                text(n_line, bold=False, spacing=4)

        text("-" * 32)

    # -------- FOOTER --------
    y -= 2 * mm
    text("PREPARE & SERVE", bold=True, center=True)

    p.showPage()
    p.save()
