from django.contrib import admin  # Django admin module for registering and managing models.

from .models import Account, Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):  # Customizes how the Branch model appears in the Django admin panel.
    list_display = ("name", "code", "city", "phone", "is_active")
    search_fields = ("name", "code", "city")
    list_filter = ("is_active", "city")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):  # Customizes how the Account model appears in the Django admin panel.
    list_display = ("account_number", "customer", "account_type", "balance", "status", "branch")
    search_fields = ("account_number", "customer__full_name", "customer__username")
    list_filter = ("account_type", "status", "branch")
    autocomplete_fields = ("customer", "branch")
    readonly_fields = ("opened_at", "updated_at")
