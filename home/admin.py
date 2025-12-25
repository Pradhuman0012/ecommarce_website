from django.contrib import admin
from .models import Category, Item, ItemSize, ContactMessage


# ---------- CATEGORY ADMIN ----------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)


# ---------- ITEM SIZE INLINE ----------
class ItemSizeInline(admin.TabularInline):
    model = ItemSize
    extra = 3
    min_num = 1


# ---------- ITEM ADMIN ----------
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "is_available",
        "created_at",
    )
    list_filter = ("category", "is_available")
    search_fields = ("name", "description")
    ordering = ("-created_at",)

    list_editable = ("is_available",)
    readonly_fields = ("created_at",)

    inlines = [ItemSizeInline]


# ---------- ITEM SIZE ADMIN (OPTIONAL BUT USEFUL) ----------
@admin.register(ItemSize)
class ItemSizeAdmin(admin.ModelAdmin):
    list_display = ("item", "size", "price")
    list_filter = ("size",)
    search_fields = ("item__name",)
    ordering = ("item", "size")


# ---------- CONTACT MESSAGE ADMIN ----------
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name", "email", "phone", "message")
    ordering = ("-created_at",)

    readonly_fields = ("name", "email", "phone", "message", "created_at")

    def has_add_permission(self, request):
        return False