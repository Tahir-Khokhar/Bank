from __future__ import annotations  # Enables postponed evaluation of type annotations.

import secrets  # Provides secure random number generation.
from decimal import Decimal  # Imports the Decimal class for precise decimal arithmetic.

from django.db import models  # Imports Django's model classes for database tables.


class Branch(models.Model):  # Represents a bank branch.

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:  # Defines metadata options for the Branch model.
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        ordering = ["name"]

    def __str__(self) -> str:  # Returns a readable string representation of the branch.
        return f"{self.name} ({self.code})"


class Account(models.Model):  # Represents a customer's bank account.

    class AccountType(models.TextChoices):  # Defines available account types.
        SAVINGS = "savings", "Savings"
        CURRENT = "current", "Current"
        FIXED = "fixed", "Fixed Deposit"
        SALARY = "salary", "Salary"

    class Status(models.TextChoices):  # Defines possible account statuses.
        ACTIVE = "active", "Active"
        FROZEN = "frozen", "Frozen"
        INACTIVE = "inactive", "Inactive"
        CLOSED = "closed", "Closed"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="accounts"
    )
    branch = models.ForeignKey(
        "accounts.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts",
    )
    account_number = models.CharField(max_length=24, unique=True, blank=True)
    account_type = models.CharField(
        max_length=20, choices=AccountType.choices, default=AccountType.SAVINGS
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    hold_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # Defines metadata options for the Account model.
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["-opened_at"]
        indexes = [
            models.Index(fields=["account_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:  # Returns a readable string representation of the account.
        return f"{self.account_number} - {self.customer.full_name}"

    @property
    def available_balance(self) -> Decimal:  # Returns the balance available after deducting held funds.
        return (self.balance or Decimal("0.00")) - (self.hold_amount or Decimal("0.00"))

    @property
    def is_operational(self) -> bool:  # Checks whether the account is active.
        return self.status == self.Status.ACTIVE

    @staticmethod
    def generate_account_number() -> str:  # Generates a unique 16-digit account number.
        while True:
            number = "".join(str(secrets.randbelow(10)) for _ in range(16))
            if not Account.objects.filter(account_number=number).exists():
                return number

    def save(self, *args, **kwargs):  # Saves the account after generating an account number if needed.
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)
