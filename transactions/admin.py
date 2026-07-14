from django.contrib import admin  # Imports Django admin module.

from .models import Transaction  # Imports the Transaction model.


@admin.register(Transaction)  # Registers the Transaction model with the Django admin site.
class TransactionAdmin(admin.ModelAdmin):  # Customizes how Transaction appears in the admin panel.

    list_display = (
        "reference",
        "account",
        "txn_type",
        "direction",
        "amount",
        "status",
        "created_at",
    )  # Displays these fields in the admin list view.

    search_fields = (
        "reference",
        "account__account_number",
        "description",
    )  # Enables searching by reference, account number, and description.

    list_filter = (
        "txn_type",
        "direction",
        "status",
        "channel",
        "created_at",
    )  # Adds filters in the admin sidebar.

    autocomplete_fields = (
        "account",
        "counterparty_account",
    )  # Enables autocomplete for related account fields.

    readonly_fields = (
        "created_at",
    )  # Makes the created_at field read-only in the admin panel.
