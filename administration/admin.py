from django.contrib import admin

from .models import CashTransaction, DailyCashCounter, Expense, Staff


class CashTransactionInline(admin.TabularInline):
    model = CashTransaction
    extra = 0


@admin.register(DailyCashCounter)
class DailyCashCounterAdmin(admin.ModelAdmin):
    list_display = ("date", "opening_balance")
    inlines = [CashTransactionInline]


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "phone", "salary", "is_active")
    list_filter = ("is_active", "role")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "amount", "description")
    list_filter = ("category",)
