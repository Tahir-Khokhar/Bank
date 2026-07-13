from django.contrib import admin  # Import Django's admin module.

from .models import Loan, LoanRepayment  # Import Loan and LoanRepayment models.


# Display LoanRepayment records inside the Loan admin page.
class LoanRepaymentInline(admin.TabularInline):
    model = LoanRepayment  # Model to display as an inline table.
    extra = 0  # Do not show extra empty forms.
    readonly_fields = ("paid_at",)  # Make the paid_at field read-only.


# Register the Loan model with the Django admin site.
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    # Fields displayed in the loan list page.
    list_display = (
        "reference",
        "customer",
        "loan_type",
        "principal_amount",
        "emi_amount",
        "status",
        "applied_at",
    )

    # Fields used for searching loans.
    search_fields = (
        "reference",
        "customer__full_name",
        "customer__username",
    )

    # Sidebar filters for the loan list page.
    list_filter = (
        "loan_type",
        "status",
        "applied_at",
    )

    # Fields that cannot be edited from the admin panel.
    readonly_fields = (
        "applied_at",
        "updated_at",
        "emi_amount",
        "total_payable",
    )

    # Display related loan repayments on the loan detail page.
    inlines = [LoanRepaymentInline]


# Register the LoanRepayment model with the Django admin site.
@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    # Fields displayed in the repayment list page.
    list_display = (
        "loan",
        "amount",
        "method",
        "paid_at",
    )

    # Enable searching repayments by loan reference.
    search_fields = (
        "loan__reference",
    )

    # Sidebar filters for repayment records.
    list_filter = (
        "method",
        "paid_at",
    )
