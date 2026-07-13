from django.contrib import admin  # Imports Django's admin module for model registration.

from .models import Customer  # Imports the Customer model.


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):  # Customizes how the Customer model appears in the Django admin panel.
    list_display = ("customer_code", "full_name", "username", "email", "phone", "is_active", "created_at")
    search_fields = ("customer_code", "full_name", "username", "email", "cnic", "phone")
    list_filter = ("is_active", "branch", "created_at")
    readonly_fields = ("created_at", "updated_at", "customer_code")
