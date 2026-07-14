"""Transaction model recording every money movement in the bank."""

from __future__ import annotations  # Postpones evaluation of type annotations until runtime.

import secrets  # Provides functions for generating secure random values.
from decimal import Decimal  # Imports Decimal for accurate financial calculations.

from django.db import models  # Imports Django's model classes.
from django.utils import timezone  # Provides timezone-aware date and time utilities.


def generate_reference(prefix: str = "TXN") -> str:
    """Return a unique, human-readable transaction reference."""
    stamp = timezone.now().strftime("%Y%m%d")  # Gets the current date and formats it as YYYYMMDD.
    while True:  # Repeats until a unique reference is generated.
        suffix = "".join(str(secrets.randbelow(10)) for _ in range(6))  # Generates a secure 6-digit random number.
        reference = f"{prefix}-{stamp}-{suffix}"  # Combines the prefix, date, and random digits.
        if not Transaction.objects.filter(reference=reference).exists():  # Checks whether the reference already exists.
            return reference  # Returns the unique transaction reference.


class Transaction(models.Model):
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

    class Status(models.TextChoices):  # Defines possible transaction statuses.
        SUCCESS = "success", "Success"
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    class Channel(models.TextChoices):  # Defines channels through which transactions occur.
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
    direction = models.CharField(max_length=10, choices=Direction.choices)  # Stores whether it is a debit or credit.
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Stores the transaction amount.
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))  # Stores any transaction fee.
    balance_after = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )  # Stores the account balance after the transaction.
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.SUCCESS
    )  # Stores the transaction status.
    channel = models.CharField(
        max_length=10, choices=Channel.choices, default=Channel.ONLINE
    )  # Stores the transaction channel.
    description = models.CharField(max_length=255, blank=True)  # Stores an optional description.
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
    )  # Links related transactions, such as transfers or reversals.
    is_reversed = models.BooleanField(default=False)  # Indicates whether the transaction has been reversed.
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically stores the creation date and time.

    class Meta:
        verbose_name = "Transaction"  # Sets the singular display name.
        verbose_name_plural = "Transactions"  # Sets the plural display name.
        ordering = ["-created_at"]  # Orders transactions by newest first.
        indexes = [
            models.Index(fields=["reference"]),  # Creates an index on the reference field.
            models.Index(fields=["txn_type"]),  # Creates an index on the transaction type.
            models.Index(fields=["status"]),  # Creates an index on the status field.
            models.Index(fields=["created_at"]),  # Creates an index on the creation date.
        ]

    def __str__(self) -> str:
        return f"{self.reference} ({self.get_txn_type_display()} {self.amount})"  # Returns a readable string representation.

    @property  # Makes the method accessible like a normal attribute.
    def signed_amount(self) -> Decimal:
        if self.direction == self.Direction.DEBIT:
            return -self.amount  # Returns a negative value for debit transactions.
        return self.amount  # Returns a positive value for credit transactions.

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference()  # Generates a unique reference before saving.
        super().save(*args, **kwargs)  # Calls the parent class save() method to store the record.
