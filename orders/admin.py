# Register your models here.
from django.contrib import admin

from .models import Order, OrderHistory, OrderItem, Recipe, RecipeItem, Table


# 1. Table Management
@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "is_occupied")
    list_filter = ("is_occupied",)
    search_fields = ("number",)


# 2. Order Items Inline (Order ke andar hi dikhega)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# 3. Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "table", "customer_name", "status", "is_billed", "created_at")
    list_filter = ("status", "is_billed", "created_at", "table")
    search_fields = ("customer_name", "id")
    inlines = [OrderItemInline]


# 4. Recipe Items Inline
class RecipeItemInline(admin.TabularInline):
    model = RecipeItem
    extra = 0


# 5. Recipe (KOT) Admin
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("order", "station", "status", "created_at")
    list_filter = ("station", "status")
    inlines = [RecipeItemInline]


# 6. Order History (Audit Trail)
@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ("bill_number", "customer_name", "total_amount", "created_at")
    readonly_fields = ("created_at",)  # History edit nahi honi chahiye
    search_fields = ("bill_number", "customer_name", "customer_phone")
