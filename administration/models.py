from decimal import Decimal

from django.db import models
from django.utils import timezone


class DailyCashCounter(models.Model):
    """
    One row per day.
    Stores the opening cash balance that the owner sets manually.
    """

    date = models.DateField(unique=True, default=timezone.now)
    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-date"]
        verbose_name = "Daily Cash Counter"
        verbose_name_plural = "Daily Cash Counters"

    def __str__(self):
        return f"Cash Counter — {self.date}"


class CashTransaction(models.Model):
    """
    Tracks cash taken OUT from the counter for supplies, expenses, etc.
    Linked to a DailyCashCounter row.
    """

    daily_counter = models.ForeignKey(
        DailyCashCounter,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"₹{self.amount} — {self.reason}"


class Staff(models.Model):
    """
    Café staff member details and salary.
    """

    name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=50,
        help_text="e.g. Barista, Chef, Waiter, Manager",
    )
    phone = models.CharField(max_length=15, blank=True, default="")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    aadhar_number = models.CharField(
        max_length=12, blank=True, default="", verbose_name="Aadhar Card Number"
    )
    photo = models.ImageField(
        upload_to="staff_photos/", blank=True, null=True, verbose_name="Photo"
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Staff"

    def __str__(self):
        return f"{self.name} ({self.role})"


class Expense(models.Model):
    """
    Tracks café expenses by category.
    """

    class Category(models.TextChoices):
        RENT = "RENT", "Rent"
        SALARY = "SALARY", "Salary"
        SUPPLIES = "SUPPLIES", "Supplies"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        MISC = "MISC", "Miscellaneous"

    date = models.DateField(default=timezone.now)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.MISC,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} — ₹{self.amount}"


class Customer(models.Model):
    """
    Stores unique customers based on phone number.
    Auto-updated whenever a bill is created.
    """

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    total_visits = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    last_visited = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_visited"]

    def __str__(self):
        return f"{self.name} ({self.phone})"
