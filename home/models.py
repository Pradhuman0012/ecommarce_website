from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="category_images/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    class Station(models.TextChoices):
        KITCHEN = "KITCHEN", "Kitchen"
        BARISTA = "BARISTA", "Barista"

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="item_images/", blank=True, null=True)

    station = models.CharField(
        max_length=20,
        choices=Station.choices,
        default=Station.KITCHEN,
        help_text="Preparation station for this item",
    )

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    def get_price_for_size(self, size: str) -> Decimal:
        """
        Return price for a given size.
        Raises ValidationError if size is invalid.
        """
        try:
            return self.sizes.get(size=size).price
        except self.sizes.model.DoesNotExist:
            raise ValidationError(f"Invalid size '{size}' for item '{self.name}'")


class ItemSize(models.Model):
    SIZE_CHOICES = (
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
    )

    item = models.ForeignKey(Item, related_name="sizes", on_delete=models.CASCADE)
    size = models.CharField(max_length=1, choices=SIZE_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("item", "size")

    def __str__(self):
        return f"{self.item.name} ({self.get_size_display()})"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"
