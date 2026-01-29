from decimal import Decimal

from django.db import models
from django.utils import timezone

from home.models import Item


class CafeConfig(models.Model):
    """
    Singleton table:
    Stores cafe-level configuration like name and GST.
    Only ONE row should exist.
    """

    cafe_name = models.CharField(max_length=200)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.cafe_name

    class Meta:
        verbose_name = "Cafe Configuration"
        verbose_name_plural = "Cafe Configuration"


class Bill(models.Model):
    """
    Represents a single customer bill / invoice.
    """

    class PaymentMode(models.TextChoices):
        CASH = "CASH", "Cash"
        UPI = "UPI", "UPI"

    bill_number = models.CharField(max_length=20, unique=True, editable=False)

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)

    # PAYMENT (AUDIT)
    payment_mode = models.CharField(
        max_length=10,
        choices=PaymentMode.choices,
        default=PaymentMode.UPI,
    )

    cash_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    change_returned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    bill_pdf_path = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bill_number

    # ---------- AUTO BILL NUMBER ----------
    def save(self, *args, **kwargs):
        if not self.bill_number:
            date_str = timezone.now().strftime("%Y%m%d")

            last_bill = (
                Bill.objects.filter(bill_number__startswith=date_str)
                .order_by("-bill_number")
                .first()
            )

            if last_bill:
                last_seq = int(last_bill.bill_number[-4:])
                new_seq = last_seq + 1
            else:
                new_seq = 1

            self.bill_number = f"{date_str}{new_seq:04d}"

        super().save(*args, **kwargs)

    # ---------- CALCULATIONS ----------
    def subtotal(self):
        return sum(item.line_total() for item in self.items.all())

    def gst_amount(self):
        taxable_amount = self.subtotal() - self.discount_amount
        if taxable_amount < 0:
            taxable_amount = Decimal("0.00")
        return taxable_amount * (self.gst_percentage / Decimal("100"))

    def total_amount(self):
        return self.subtotal() - self.discount_amount + self.gst_amount()


class BillItem(models.Model):
    """
    Line items inside a bill.
    """

    SIZE_CHOICES = (
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
    )

    bill = models.ForeignKey(Bill, related_name="items", on_delete=models.CASCADE)

    item = models.ForeignKey(Item, on_delete=models.PROTECT)

    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default="M")

    price = models.DecimalField(max_digits=8, decimal_places=2)

    quantity = models.PositiveIntegerField()

    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.item.name} ({self.size}) x {self.quantity}"
