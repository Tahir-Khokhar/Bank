# Enable postponed evaluation of type hints (improves type hint support)
from __future__ import annotations

# Import timedelta for date calculations
from datetime import timedelta

# Import Decimal for precise decimal calculations
from decimal import Decimal

# Import Django database query functions
from django.db.models import Count, DecimalField, Q, Sum

# Import database functions for handling NULL values and grouping by month
from django.db.models.functions import Coalesce, TruncMonth

# Import Django timezone utilities
from django.utils import timezone

# Import the Account model
from accounts.models import Account

# Import the Customer model
from customers.models import Customer

# Import the Employee model
from employees.models import Employee

# Import the Loan model
from loans.models import Loan

# Import the Transaction model
from transactions.models import Transaction

# Store month names for chart labels
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Define a reusable zero decimal value
_ZERO = Decimal("0.00")

# Define a decimal field used for aggregate calculations
_DEC = DecimalField(max_digits=18, decimal_places=2)


# Calculate the sum of a field in a queryset
def _sum(qs, field="amount"):
    # Aggregate the total value and replace NULL with zero
    return qs.aggregate(t=Coalesce(Sum(field), _ZERO, output_field=_DEC))["t"] or _ZERO


# Return the last n months with year, month number, and label
def last_n_months(n=6):
    """Return a list of (year, month, label) tuples for the last ``n`` months."""

    # Get the first day of the current month
    today = timezone.now().date().replace(day=1)

    # Store month information
    months = []

    # Extract current year and month
    y, m = today.year, today.month

    # Loop through the last n months
    for _ in range(n):
        # Save year, month number, and month name
        months.append((y, m, MONTHS[m - 1]))

        # Move to the previous month
        m -= 1

        # Move to previous year if needed
        if m == 0:
            m = 12
            y -= 1

    # Return months in chronological order
    return list(reversed(months))


# Generate monthly credit and debit totals
def monthly_transaction_series(n=6, account=None):
    """Return labels + credit/debit totals per month for the last ``n`` months."""

    # Get successful transactions only
    qs = Transaction.objects.filter(status=Transaction.Status.SUCCESS)

    # Filter by account if provided
    if account is not None:
        qs = qs.filter(account=account)

    # Get the last n months
    months = last_n_months(n)

    # Store chart data
    labels, credit, debit = [], [], []

    # Process each month
    for y, m, label in months:

        # Filter transactions for the month
        month_qs = qs.filter(created_at__year=y, created_at__month=m)

        # Add month label
        labels.append(label)

        # Calculate monthly credit total
        credit.append(float(_sum(month_qs.filter(direction=Transaction.Direction.CREDIT))))

        # Calculate monthly debit total
        debit.append(float(_sum(month_qs.filter(direction=Transaction.Direction.DEBIT))))

    # Return chart data
    return {"labels": labels, "credit": credit, "debit": debit}


# Generate monthly record counts
def monthly_count_series(qs, date_field, n=6):
    """Return labels + counts per month for a queryset."""

    # Get the last n months
    months = last_n_months(n)

    # Initialize chart data
    labels, data, cumulative, running = [], [], [], 0

    # Count records before the first month
    base = qs.filter(**{f"{date_field}__lt": _month_start(months[0])}).count()

    # Start cumulative count
    running = base

    # Process each month
    for entry in months:
        y, m, label = entry

        # Count records created in this month
        count = qs.filter(**{
            f"{date_field}__year": y,
            f"{date_field}__month": m
        }).count()

        # Update cumulative total
        running += count

        # Store chart values
        labels.append(label)
        data.append(count)
        cumulative.append(running)

    # Return chart data
    return {"labels": labels, "data": data, "cumulative": cumulative}


# Return the first day of a given month
def _month_start(entry):
    y, m, _ = entry

    # Create a timezone-aware datetime object
    return timezone.datetime(y, m, 1, tzinfo=timezone.get_current_timezone())


# Generate daily transaction counts
def daily_transaction_series(days=7, branch=None):

    # Store chart labels and values
    labels, data = [], []

    # Get today's date
    today = timezone.now().date()

    # Process each day
    for i in range(days - 1, -1, -1):

        # Calculate the date
        day = today - timedelta(days=i)

        # Get transactions for the day
        qs = Transaction.objects.filter(created_at__date=day)

        # Store weekday name
        labels.append(day.strftime("%a"))

        # Store transaction count
        data.append(qs.count())

    # Return chart data
    return {"labels": labels, "data": data}


# Generate loan status statistics
def loan_status_breakdown():

    # Count loans grouped by status
    counts = {
        row["status"]: row["c"]
        for row in Loan.objects.values("status").annotate(c=Count("id"))
    }

    # Get readable status labels
    labels_map = dict(Loan.Status.choices)

    # Store chart data
    labels, data = [], []

    # Process each loan status
    for status, label in Loan.Status.choices:
        if counts.get(status):
            labels.append(label)
            data.append(counts[status])

    # Return chart data
    return {"labels": labels, "data": data}


# Return zero if the value is empty
def money(value):
    return value or _ZERO


# Generate bank-wide statistics
def bank_wide_stats():

    # Get Account model manager
    accounts = Account.objects

    # Get Loan model manager
    loans = Loan.objects

    # Get today's date
    today = timezone.now().date()

    # Get successful transactions
    success = Transaction.objects.filter(status=Transaction.Status.SUCCESS)

    # Calculate total deposits
    total_deposits = _sum(success.filter(
        Q(txn_type=Transaction.Type.DEPOSIT) |
        Q(direction=Transaction.Direction.CREDIT,
          txn_type=Transaction.Type.TRANSFER)))

    # Calculate total withdrawals
    total_withdrawals = _sum(success.filter(
        Q(txn_type=Transaction.Type.WITHDRAWAL) |
        Q(direction=Transaction.Direction.DEBIT,
          txn_type=Transaction.Type.TRANSFER)))

    # Initialize revenue
    revenue = _ZERO

    # Calculate revenue from loan interest
    for loan in loans.filter(status__in=[
        Loan.Status.ACTIVE,
        Loan.Status.DISBURSED,
        Loan.Status.CLOSED
    ]):
        revenue += (loan.total_payable or _ZERO) - (loan.principal_amount or _ZERO)

    # Return all dashboard statistics
    return {
        "total_customers": Customer.objects.count(),
        "active_customers": Customer.objects.filter(is_active=True).count(),
        "total_employees": Employee.objects.count(),
        "total_accounts": accounts.count(),
        "active_accounts": accounts.filter(status=Account.Status.ACTIVE).count(),
        "inactive_accounts": accounts.exclude(status=Account.Status.ACTIVE).count(),
        "total_balance": _sum(accounts.all(), "balance"),
        "total_transactions": Transaction.objects.count(),
        "today_transactions": Transaction.objects.filter(created_at__date=today).count(),
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "active_loans": loans.filter(status__in=[Loan.Status.ACTIVE, Loan.Status.DISBURSED]).count(),
        "pending_loans": loans.filter(status__in=[Loan.Status.PENDING, Loan.Status.UNDER_REVIEW]).count(),
        "approved_loans": loans.filter(status=Loan.Status.APPROVED).count(),
        "rejected_loans": loans.filter(status=Loan.Status.REJECTED).count(),
        "total_loan_portfolio": _sum(
            loans.filter(status__in=[Loan.Status.ACTIVE, Loan.Status.DISBURSED]),
            "principal_amount"
        ),
        "bank_revenue": revenue.quantize(_ZERO),
    }


# Generate employee dashboard statistics
def employee_stats():

    # Get today's date
    today = timezone.now().date()

    # Get successful transactions
    success = Transaction.objects.filter(status=Transaction.Status.SUCCESS)

    # Return employee dashboard statistics
    return {
        "total_customers": Customer.objects.count(),
        "today_transactions": Transaction.objects.filter(created_at__date=today).count(),
        "pending_loans": Loan.objects.filter(
            status__in=[Loan.Status.PENDING, Loan.Status.UNDER_REVIEW]
        ).count(),
        "active_loans": Loan.objects.filter(
            status__in=[Loan.Status.ACTIVE, Loan.Status.DISBURSED]
        ).count(),
        "total_deposits": _sum(success.filter(txn_type=Transaction.Type.DEPOSIT)),
        "total_withdrawals": _sum(success.filter(txn_type=Transaction.Type.WITHDRAWAL)),
        "failed_transactions": Transaction.objects.filter(
            status=Transaction.Status.FAILED
        ).count(),
    }
