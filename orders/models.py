from decimal import Decimal

from django.db import models
from django.utils import timezone


class Table(models.Model):
    number = models.CharField(max_length=10, unique=True)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Table {self.number}"


class Station(models.TextChoices):
    KITCHEN = "KITCHEN", "Kitchen"
    BARISTA = "BARISTA", "Barista"


class Order(models.Model):
    table = models.ForeignKey(
        Table, on_delete=models.CASCADE, related_name="orders", null=True
    )
    bill = models.ForeignKey(
        "billing.Bill",
        on_delete=models.SET_NULL,  # Bill delete ho to order delete na ho
        related_name="orders",
        null=True,
        blank=True,
    )
    customer_name = models.CharField(max_length=255)
    is_billed = models.BooleanField(
        default=False
    )  # Ye track karega ki iska bill ban chuka hai ya nahi
    created_at = models.DateTimeField(default=timezone.now)

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SERVED = "SERVED", "Served"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    def __str__(self) -> str:
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        "home.Item",
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, default="REGULAR")
    priority = models.PositiveSmallIntegerField(
        help_text="Lower number = served first",
        default=1,
    )
    is_sent_to_kitchen = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.item.name} x{self.quantity}"


class Recipe(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="recipes",
        on_delete=models.CASCADE,
    )
    station = models.CharField(
        max_length=20,
        choices=Station.choices,
    )

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("order", "station")


class RecipeItem(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="items",
        on_delete=models.CASCADE,
    )
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    size = models.CharField(max_length=10, blank=True, default="")
    priority = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["priority"]


class OrderHistory(models.Model):
    """
    Immutable audit snapshot of an order at billing time.
    This table is APPEND-ONLY.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")

    # -------- IDENTITY --------
    bill_number = models.CharField(max_length=30, default="UNKNOWN")

    customer_name = models.CharField(max_length=100, default="UNKNOWN")

    customer_phone = models.CharField(max_length=15, default="NA")

    # -------- PAYMENT --------
    PAYMENT_MODES = (
        ("CASH", "Cash"),
        ("UPI", "UPI"),
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODES,
        default="CASH",
    )

    cash_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        null=True,
        blank=True,
    )

    change_returned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        null=True,
        blank=True,
    )

    # -------- AMOUNTS --------
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    gst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    # -------- ITEMS SNAPSHOT --------
    items_snapshot = models.JSONField(default=list)

    # -------- PDF --------
    bill_pdf_path = models.CharField(max_length=255, blank=True, default="")

    # -------- META --------
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order History"
        verbose_name_plural = "Order History"

    def __str__(self) -> str:
        return f"Order #{self.order_id} | {self.bill_number}"
