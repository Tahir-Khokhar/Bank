from django.contrib import admin  # Imports Django's admin module.

from .models import Employee  # Imports the Employee model.


@admin.register(Employee)  # Registers the Employee model with the Django admin site.
class EmployeeAdmin(admin.ModelAdmin):  # Customizes the Employee model in the admin panel.

    list_display = (
        "employee_code",
        "full_name",
        "username",
        "role",
        "is_active",
        "is_suspended",
        "branch",
    )  # Displays these fields in the admin list view.

    search_fields = (
        "employee_code",
        "full_name",
        "username",
        "email",
    )  # Enables searching by employee code, name, username, and email.

    list_filter = (
        "role",
        "is_active",
        "is_suspended",
        "branch",
    )  # Adds filters in the admin sidebar.

    readonly_fields = (
        "created_at",
        "updated_at",
        "employee_code",
    )  # Makes these fields read-only in the admin panel.
