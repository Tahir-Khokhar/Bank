# Enable postponed evaluation of type hints
from __future__ import annotations

# Import Decimal for accurate money calculations
from decimal import Decimal

# Import Django database transaction support
from django.db import transaction as db_transaction

# Import Django timezone utilities
from django.utils import timezone

# Import ActivityLog and Notification models
from dashboard.models import ActivityLog, Notification


# -------------------- Notification Functions --------------------


# Create a notification for a customer
def notify_customer(customer, title, message="", category=Notification.Category.SYSTEM, url=""):

    # Return nothing if no customer is provided
    if not customer:
        return None

    # Create and save the notification
    return Notification.objects.create(
        audience=Notification.Audience.CUSTOMER,
        customer=customer,
        category=category,
        title=title,
        message=message,
        url=url,
    )


# Create a notification for an employee
def notify_employee(employee, title, message="", category=Notification.Category.SYSTEM, url=""):

    # Return nothing if no employee is provided
    if not employee:
        return None

    # Create and save the notification
    return Notification.objects.create(
        audience=Notification.Audience.EMPLOYEE,
        employee=employee,
        category=category,
        title=title,
        message=message,
        url=url,
    )


# Send a notification to all active managers
def notify_all_managers(title, message="", category=Notification.Category.SYSTEM, url=""):

    # Import Employee model
    from employees.models import Employee

    # Get all active managers
    managers = Employee.objects.filter(
        role=Employee.Role.MANAGER,
        is_active=True
    )

    # Send a notification to every manager
    return [
        notify_employee(m, title, message, category, url)
        for m in managers
    ]


# -------------------- Activity Log --------------------


# Save an activity log entry
def log_activity(
    *,
    action,
    category=ActivityLog.Category.SYSTEM,
    customer=None,
    employee=None,
    actor_role="",
    actor_name="",
    ip_address=None,
):

    # Fill actor details for employees
    if employee and not actor_name:
        actor_name = employee.full_name
        actor_role = actor_role or (
            "manager" if employee.is_manager else "employee"
        )

    # Fill actor details for customers
    elif customer and not actor_name:
        actor_name = customer.full_name
        actor_role = actor_role or "customer"

    # Create the activity log
    return ActivityLog.objects.create(
        actor_role=actor_role or "system",
        actor_name=actor_name or "System",
        customer=customer,
        employee=employee,
        category=category,
        action=action,
        ip_address=ip_address,
    )


# -------------------- Banking Operations --------------------


# Custom exception for banking errors
class BankingError(Exception):
    """Raised when a banking operation cannot be completed."""


# Convert a value into a decimal with two decimal places
def _q(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


# Deposit money into an account
def deposit(
    account,
    amount,
    *,
    employee=None,
    channel=None,
    description="Cash deposit"
):
    """Credit amount to an account."""

    # Import Transaction model
    from transactions.models import Transaction

    # Format the amount
    amount = _q(amount)

    # Check that the amount is valid
    if amount <= 0:
        raise BankingError("Amount must be greater than zero.")

    # Prevent deposits into closed accounts
    if account.status == account.Status.CLOSED:
        raise BankingError("This account is closed.")

    # Execute the operation as a single database transaction
    with db_transaction.atomic():

        # Increase account balance
        account.balance = _q(account.balance) + amount

        # Save updated balance
        account.save(update_fields=["balance", "updated_at"])

        # Record the transaction
        txn = Transaction.objects.create(
            account=account,
            txn_type=Transaction.Type.DEPOSIT,
            direction=Transaction.Direction.CREDIT,
            amount=amount,
            balance_after=account.balance,
            status=Transaction.Status.SUCCESS,
            channel=channel or Transaction.Channel.ONLINE,
            description=description,
            created_by_employee=employee,
        )

    # Notify the customer
    notify_customer(
        account.customer,
        "Deposit received",
        f"{amount} was credited to account {account.account_number}.",
        Notification.Category.TRANSACTION,
        url="/transactions/",
    )

    return txn


# Withdraw money from an account
def withdraw(
    account,
    amount,
    *,
    employee=None,
    channel=None,
    description="Cash withdrawal"
):
    """Debit amount from an account."""

    from transactions.models import Transaction

    # Format the amount
    amount = _q(amount)

    # Validate amount
    if amount <= 0:
        raise BankingError("Amount must be greater than zero.")

    # Check account status
    if account.status != account.Status.ACTIVE:
        raise BankingError(
            f"Account is not active (status: {account.get_status_display()})."
        )

    # Check available balance
    if amount > account.available_balance:
        raise BankingError("Insufficient available balance.")

    # Execute safely
    with db_transaction.atomic():

        # Reduce account balance
        account.balance = _q(account.balance) - amount

        # Save updated balance
        account.save(update_fields=["balance", "updated_at"])

        # Record the withdrawal
        txn = Transaction.objects.create(
            account=account,
            txn_type=Transaction.Type.WITHDRAWAL,
            direction=Transaction.Direction.DEBIT,
            amount=amount,
            balance_after=account.balance,
            status=Transaction.Status.SUCCESS,
            channel=channel or Transaction.Channel.ONLINE,
            description=description,
            created_by_employee=employee,
        )

    # Notify the customer
    notify_customer(
        account.customer,
        "Withdrawal processed",
        f"{amount} was debited from account {account.account_number}.",
        Notification.Category.TRANSACTION,
        url="/transactions/",
    )

    return txn


# Transfer money between two accounts
def transfer(
    source,
    destination,
    amount,
    *,
    employee=None,
    channel=None,
    description=""
):
    """Transfer money between accounts."""

    from transactions.models import Transaction

    # Format amount
    amount = _q(amount)

    # Validate transfer
    if amount <= 0:
        raise BankingError("Amount must be greater than zero.")

    if source.pk == destination.pk:
        raise BankingError("Source and destination accounts must differ.")

    if source.status != source.Status.ACTIVE:
        raise BankingError("Source account is not active.")

    if destination.status == destination.Status.CLOSED:
        raise BankingError("Destination account is closed.")

    if amount > source.available_balance:
        raise BankingError("Insufficient available balance.")

    # Execute transfer safely
    with db_transaction.atomic():

        # Deduct money from source account
        source.balance = _q(source.balance) - amount
        source.save(update_fields=["balance", "updated_at"])

        # Record debit transaction
        debit = Transaction.objects.create(
            account=source,
            counterparty_account=destination,
            txn_type=Transaction.Type.TRANSFER,
            direction=Transaction.Direction.DEBIT,
            amount=amount,
            balance_after=source.balance,
            status=Transaction.Status.SUCCESS,
            channel=channel or Transaction.Channel.ONLINE,
            description=description or f"Transfer to {destination.account_number}",
            created_by_employee=employee,
        )

        # Add money to destination account
        destination.balance = _q(destination.balance) + amount
        destination.save(update_fields=["balance", "updated_at"])

        # Record credit transaction
        credit = Transaction.objects.create(
            account=destination,
            counterparty_account=source,
            txn_type=Transaction.Type.TRANSFER,
            direction=Transaction.Direction.CREDIT,
            amount=amount,
            balance_after=destination.balance,
            status=Transaction.Status.SUCCESS,
            channel=channel or Transaction.Channel.ONLINE,
            description=description or f"Transfer from {source.account_number}",
            created_by_employee=employee,
            related_transaction=debit,
        )

        # Link both transactions together
        debit.related_transaction = credit
        debit.save(update_fields=["related_transaction"])

    # Notify sender
    notify_customer(
        source.customer,
        "Transfer sent",
        f"{amount} sent to {destination.account_number}.",
        Notification.Category.TRANSACTION,
        url="/transactions/",
    )

    # Notify receiver
    notify_customer(
        destination.customer,
        "Transfer received",
        f"{amount} received from {source.account_number}.",
        Notification.Category.TRANSACTION,
        url="/transactions/",
    )

    return debit


# Reverse a completed transaction
def reverse_transaction(txn, *, employee=None):
    """Reverse a successful deposit or withdrawal."""

    from transactions.models import Transaction

    # Prevent duplicate reversals
    if txn.is_reversed or txn.status == Transaction.Status.REVERSED:
        raise BankingError("Transaction is already reversed.")

    # Allow only deposits and withdrawals
    if txn.txn_type not in {
        Transaction.Type.DEPOSIT,
        Transaction.Type.WITHDRAWAL,
    }:
        raise BankingError(
            "Only deposits and withdrawals can be reversed here."
        )

    # Get the related account
    account = txn.account

    # Execute reversal safely
    with db_transaction.atomic():

        # Reverse a credit transaction
        if txn.direction == Transaction.Direction.CREDIT:

            # Ensure enough balance exists
            if _q(txn.amount) > account.available_balance:
                raise BankingError(
                    "Insufficient balance to reverse this credit."
                )

            account.balance = _q(account.balance) - _q(txn.amount)
            new_direction = Transaction.Direction.DEBIT

        # Reverse a debit transaction
        else:
            account.balance = _q(account.balance) + _q(txn.amount)
            new_direction = Transaction.Direction.CREDIT

        # Save updated balance
        account.save(update_fields=["balance", "updated_at"])

        # Create reversal transaction
        reversal = Transaction.objects.create(
            account=account,
            txn_type=Transaction.Type.REVERSAL,
            direction=new_direction,
            amount=_q(txn.amount),
            balance_after=account.balance,
            status=Transaction.Status.SUCCESS,
            channel=Transaction.Channel.SYSTEM,
            description=f"Reversal of {txn.reference}",
            created_by_employee=employee,
            related_transaction=txn,
        )

        # Mark original transaction as reversed
        txn.is_reversed = True
        txn.status = Transaction.Status.REVERSED
        txn.save(update_fields=["is_reversed", "status"])

    # Notify customer
    notify_customer(
        account.customer,
        "Transaction reversed",
        f"Transaction {txn.reference} was reversed.",
        Notification.Category.TRANSACTION,
        url="/transactions/",
    )

    return reversal
