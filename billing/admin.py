from django.contrib import admin

from .models import Bill, BillItem, CafeConfig

# Register your models here.
# superuser: admin@mtc.com  password: mtc@1234


# ---------- INLINE BILL ITEMS ----------
class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1
    fields = ("item", "price", "quantity", "line_total")
    readonly_fields = ("line_total",)

    def line_total(self, obj):
        if obj.pk:
            return obj.line_total()
        return "-"

    line_total.short_description = "Line Total"


# ---------- BILL ADMIN ----------
@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "bill_number",
        "customer_name",
        "customer_phone",
        "subtotal_display",
        "discount_amount",
        "gst_amount_display",
        "total_amount_display",
        "created_at",
    )

    readonly_fields = (
        "bill_number",
        "created_at",
        "subtotal_display",
        "gst_amount_display",
        "total_amount_display",
    )

    inlines = [BillItemInline]

    search_fields = ("bill_number", "customer_name", "customer_phone")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    # ---------- DISPLAY HELPERS ----------
    def subtotal_display(self, obj):
        return obj.subtotal()

    subtotal_display.short_description = "Subtotal"

    def gst_amount_display(self, obj):
        return obj.gst_amount()

    gst_amount_display.short_description = "GST Amount"

    def total_amount_display(self, obj):
        return obj.total_amount()

    total_amount_display.short_description = "Total Amount"


# ---------- CAFE CONFIG ----------
@admin.register(CafeConfig)
class CafeConfigAdmin(admin.ModelAdmin):
    list_display = ("cafe_name", "gst_percentage")

    def has_add_permission(self, request):
        # Allow only ONE config row
        if CafeConfig.objects.exists():
            return False
        return True
