from __future__ import annotations  # Allows using future-style type hints.

import secrets  # Used to generate random secure numbers.
from decimal import Decimal, ROUND_HALF_UP  # Used for accurate decimal calculations.

from django.db import models  # Import Django model classes.
from django.utils import timezone  # Import timezone utilities.


# Generate a unique loan reference number.
def generate_loan_reference() -> str:
    stamp = timezone.now().strftime("%Y%m")  # Get current year and month.

    while True:  # Keep trying until a unique reference is created.
        suffix = "".join(str(secrets.randbelow(10)) for _ in range(6))  # Generate a 6-digit random number.
        reference = f"LN-{stamp}-{suffix}"  # Create the loan reference.

        if not Loan.objects.filter(reference=reference).exists():  # Check if reference already exists.
            return reference  # Return the unique reference.


# Loan model stores all loan information.
class Loan(models.Model):

    """Represents a customer's loan application."""

    # Available loan types.
    class LoanType(models.TextChoices):
        PERSONAL = "personal", "Personal Loan"
        HOME = "home", "Home Loan"
        CAR = "car", "Car Loan"
        BUSINESS = "business", "Business Loan"
        EDUCATION = "education", "Education Loan"

    # Available loan statuses.
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        DISBURSED = "disbursed", "Disbursed"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        DEFAULTED = "defaulted", "Defaulted"

    OPEN_STATUSES = {Status.DISBURSED, Status.ACTIVE}  # Statuses considered active.

    reference = models.CharField(max_length=40, unique=True, blank=True)  # Unique loan reference.

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,  # Delete loans if customer is deleted.
        related_name="loans",  # Access loans using customer.loans.
    )

    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.SET_NULL,  # Keep loan if account is deleted.
        null=True,
        blank=True,
        related_name="loans",
    )

    loan_type = models.CharField(
        max_length=20,
        choices=LoanType.choices,  # Display predefined loan types.
        default=LoanType.PERSONAL,
    )

    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)  # Loan amount.

    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("12.00"),
        help_text="Annual interest rate (%)",  # Help message in admin.
    )

    tenure_months = models.PositiveIntegerField(default=12)  # Loan duration.

    emi_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
    )  # Monthly EMI.

    total_payable = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
    )  # Total amount to repay.

    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
    )  # Amount already paid.

    purpose = models.CharField(max_length=255, blank=True)  # Purpose of the loan.

    status = models.CharField(
        max_length=20,
        choices=Status.choices,  # Display predefined statuses.
        default=Status.PENDING,
    )

    reviewed_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_loans",
    )

    approved_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_loans",
    )

    decision_note = models.CharField(max_length=255, blank=True)  # Review remarks.

    applied_at = models.DateTimeField(auto_now_add=True)  # Set when record is created.
    decided_at = models.DateTimeField(null=True, blank=True)  # Approval date.
    disbursed_at = models.DateTimeField(null=True, blank=True)  # Disbursement date.
    updated_at = models.DateTimeField(auto_now=True)  # Update automatically on every save.

    class Meta:
        verbose_name = "Loan"  # Singular model name.
        verbose_name_plural = "Loans"  # Plural model name.
        ordering = ["-applied_at"]  # Show newest loans first.
        indexes = [
            models.Index(fields=["reference"]),  # Database index for reference.
            models.Index(fields=["status"]),  # Database index for status.
        ]

    def __str__(self):
        return f"{self.reference} - {self.customer.full_name}"  # String representation.

    # Calculate EMI and total repayment.
    def compute_schedule(self):
        principal = Decimal(self.principal_amount or 0)
        months = int(self.tenure_months or 0)
        annual_rate = Decimal(self.interest_rate or 0)

        if principal <= 0 or months <= 0:
            self.emi_amount = Decimal("0.00")
            self.total_payable = principal
            return

        monthly_rate = annual_rate / Decimal("1200")

        if monthly_rate == 0:
            emi = principal / months
        else:
            factor = (Decimal(1) + monthly_rate) ** months
            emi = principal * monthly_rate * factor / (factor - Decimal(1))

        self.emi_amount = emi.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        self.total_payable = (
            self.emi_amount * months
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def remaining_amount(self):
        """Return remaining balance."""
        return (self.total_payable or Decimal("0.00")) - (
            self.amount_paid or Decimal("0.00")
        )

    @property
    def progress_percent(self):
        """Return repayment percentage."""
        if not self.total_payable:
            return 0

        pct = (self.amount_paid / self.total_payable) * 100
        return int(min(pct, 100))

    @property
    def is_open(self):
        """Return True if loan is active."""
        return self.status in self.OPEN_STATUSES

    def save(self, *args, **kwargs):
        """Generate reference and EMI before saving."""
        if not self.reference:
            self.reference = generate_loan_reference()

        if not self.emi_amount or not self.total_payable:
            self.compute_schedule()

        super().save(*args, **kwargs)


# Stores each loan repayment.
class LoanRepayment(models.Model):

    """Represents a single loan payment."""

    class Method(models.TextChoices):
        ACCOUNT = "account", "Account Debit"
        CASH = "cash", "Cash"
        ONLINE = "online", "Online"

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,  # Delete repayments if loan is deleted.
        related_name="repayments",  # Access repayments using loan.repayments.
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Payment amount.

    method = models.CharField(
        max_length=10,
        choices=Method.choices,  # Available payment methods.
        default=Method.ACCOUNT,
    )

    reference = models.CharField(max_length=40, blank=True)  # Payment reference.

    recorded_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_repayments",
    )

    paid_at = models.DateTimeField(auto_now_add=True)  # Payment date.

    class Meta:
        verbose_name = "Loan Repayment"  # Singular name.
        verbose_name_plural = "Loan Repayments"  # Plural name.
        ordering = ["-paid_at"]  # Show latest payments first.

    def __str__(self):
        return f"{self.loan.reference} - {self.amount}"  # String representation.
