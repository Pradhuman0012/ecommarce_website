# orders/utils/pdf.py
from io import BytesIO
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas


def generate_recipe_pdf(recipe) -> BytesIO:
    buffer = BytesIO()

    width = 80 * mm
    height = 160 * mm
    p = canvas.Canvas(buffer, pagesize=(width, height))
    y = height - 10 * mm

    def line(text):
        nonlocal y
        p.drawString(5 * mm, y, text)
        y -= 5 * mm

    line(f"{recipe.station} ORDER")
    line("-" * 20)
    line(f"Order #{recipe.order.id}")
    line("-" * 20)

    for item in recipe.items.all():
        line(f"{item.item_name} x{item.quantity}")
        if item.notes:
            line(f"  * {item.notes}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer
