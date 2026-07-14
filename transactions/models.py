"""Transaction model recording every money movement in the bank."""

from __future__ import annotations  # Postpones evaluation of type annotations until runtime.

import secrets  # Provides secure random number generation.
from decimal import Decimal  # Used for precise decimal calculations.

from django.db import models  # Imports Django model classes.
from django.utils import timezone  # Imports timezone-aware date and time functions.


def generate_reference(prefix: str = "TXN") -> str:  # Generates a unique transaction reference.
    """Return a unique, human-readable transaction reference."""
    stamp = timezone.now().strftime("%Y%m%d")  # Gets the current date and formats it as YYYYMMDD.
    while True:  # Continues until a unique reference is created.
        suffix = "".join(str(secrets.randbelow(10)) for _ in range(6))  # Generates a random 6-digit number.
        reference = f"{prefix}-{stamp}-{suffix}"  # Combines prefix, date, and random digits.
        if not Transaction.objects.filter(reference=reference).exists():  # Checks if the reference already exists.
            return reference  # Returns the unique transaction reference.


class Transaction(models.Model):  # Model for storing transaction records.
    """A single ledger entry against an account.

    Transfers create two linked entries (a debit and a credit) so that each
    account keeps an accurate, auditable running balance.
    """

    class Type(models.TextChoices):  # Defines available transaction types.
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        TRANSFER = "transfer", "Transfer"
        FEE = "fee", "Fee"
        LOAN_DISBURSEMENT = "loan_disbursement", "Loan Disbursement"
        LOAN_REPAYMENT = "loan_repayment", "Loan Repayment"
        REVERSAL = "reversal", "Reversal"

    class Direction(models.TextChoices):  # Defines transaction directions.
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    class Status(models.TextChoices):  # Defines transaction statuses.
        SUCCESS = "success", "Success"
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    class Channel(models.TextChoices):  # Defines transaction channels.
        ONLINE = "online", "Online"
        TELLER = "teller", "Teller"
        ATM = "atm", "ATM"
        SYSTEM = "system", "System"

    reference = models.CharField(max_length=40, unique=True, blank=True)  # Stores the unique transaction reference.
    account = models.ForeignKey(
        "accounts.Account", on_delete=models.CASCADE, related_name="transactions"
    )  # Links the transaction to an account.

    counterparty_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counterparty_transactions",
    )  # Stores the other account involved in a transfer.

    txn_type = models.CharField(max_length=20, choices=Type.choices)  # Stores the transaction type.
    direction = models.CharField(max_length=10, choices=Direction.choices)  # Stores whether the transaction is a debit or credit.
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Stores the transaction amount.
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))  # Stores the transaction fee.
    balance_after = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )  # Stores the account balance after the transaction.

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.SUCCESS
    )  # Stores the transaction status.

    channel = models.CharField(
        max_length=10, choices=Channel.choices, default=Channel.ONLINE
    )  # Stores the transaction channel.

    description = models.CharField(max_length=255, blank=True)  # Stores an optional transaction description.

    created_by_employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_transactions",
    )  # Stores the employee who created the transaction.

    related_transaction = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_entries",
    )  # Links related transactions such as transfers or reversals.

    is_reversed = models.BooleanField(default=False)  # Indicates whether the transaction has been reversed.
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically stores the creation date and time.

    class Meta:  # Defines model metadata.
        verbose_name = "Transaction"  # Singular name in Django admin.
        verbose_name_plural = "Transactions"  # Plural name in Django admin.
        ordering = ["-created_at"]  # Orders transactions from newest to oldest.
        indexes = [
            models.Index(fields=["reference"]),  # Creates an index on the reference field.
            models.Index(fields=["txn_type"]),  # Creates an index on the transaction type field.
            models.Index(fields=["status"]),  # Creates an index on the status field.
            models.Index(fields=["created_at"]),  # Creates an index on the created_at field.
        ]

    def __str__(self) -> str:  # Returns a readable string representation of the transaction.
        return f"{self.reference} ({self.get_txn_type_display()} {self.amount})"

    @property  # Allows signed_amount to be accessed like a normal attribute.
    def signed_amount(self) -> Decimal:
        if self.direction == self.Direction.DEBIT:
            return -self.amount  # Returns a negative amount for debit transactions.
        return self.amount  # Returns a positive amount for credit transactions.

    def save(self, *args, **kwargs):  # Saves the transaction to the database.
        if not self.reference:
            self.reference = generate_reference()  # Generates a reference if one does not exist.
        super().save(*args, **kwargs)  # Calls the parent save() method to save the object.
