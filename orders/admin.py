from django.contrib import admin
from django.template.defaultfilters import truncatechars

from .models import Order, OrderHistory, OrderItem, Recipe, RecipeItem


# --- Inlines ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("item", "quantity", "priority", "notes")  # Notes yahan bhi dikhenge


class RecipeItemInline(admin.TabularInline):
    model = RecipeItem
    extra = 0
    fields = ("item_name", "quantity", "priority", "notes")


# --- Admin Classes ---


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # List display mein items ke saath unke notes bhi
    list_display = (
        "id",
        "customer_name",
        "display_items_with_notes",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "id")
    inlines = [OrderItemInline]

    def display_items_with_notes(self, obj):
        items = obj.items.all()
        display_text = []
        for i in items:
            text = f"{i.item.name} (x{i.quantity})"
            if i.notes:
                # Notes ko bracket mein dikhayega
                text += f" [Note: {i.notes}]"
            display_text.append(text)

        # Agar notes bade hain toh 100 characters ke baad ... dikhayega
        full_string = ", ".join(display_text)
        return truncatechars(full_string, 100)

    display_items_with_notes.short_description = "Items & Special Notes"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "station", "display_recipe_with_notes", "status")
    list_filter = ("station", "status")
    inlines = [RecipeItemInline]

    def display_recipe_with_notes(self, obj):
        items = obj.items.all()
        display_text = []
        for i in items:
            text = f"{i.item_name} (x{i.quantity})"
            if i.notes:
                text += f" - ({i.notes})"
            display_text.append(text)

        return truncatechars(", ".join(display_text), 100)

    display_recipe_with_notes.short_description = "Recipe Details (Notes)"


@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ("bill_number", "customer_name", "total_amount", "created_at")

    # Safety: No editing history
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Optional: Seedha items dekhne ke liye
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "item", "quantity", "notes", "priority")
    list_filter = ("order__status",)
