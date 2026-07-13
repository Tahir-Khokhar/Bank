from __future__ import annotations  # Enables postponed evaluation of type annotations.

import secrets  # Provides secure random number generation.

from django.db import models  # Imports Django model classes for database tables.
from django.contrib.auth.hashers import make_password, check_password  # Imports password hashing and verification functions.


class Customer(models.Model):  # Represents a bank customer.

    # --- Authentication (existing fields, do not remove) ---------------
    full_name = models.CharField(max_length=150)  # Stores the customer's full name.
    username = models.CharField(max_length=150, unique=True)  # Stores a unique username.
    email = models.EmailField(max_length=254, unique=True)  # Stores a unique email address.
    password = models.CharField(max_length=255)  # Stores the hashed password.

    # --- Profile ------------------------------------------------------
    customer_code = models.CharField(max_length=20, unique=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    cnic = models.CharField("CNIC / National ID", max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    monthly_income = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    employer_name = models.CharField(max_length=150, blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/customers/", null=True, blank=True
    )
    branch = models.ForeignKey(
        "accounts.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
    )

    is_active = models.BooleanField(default=True)  # Indicates whether the customer account is active.
    created_at = models.DateTimeField(auto_now_add=True)  # Stores the account creation time.
    updated_at = models.DateTimeField(auto_now=True)  # Stores the last update time.

    class Meta:  # Defines metadata options for the Customer model.
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # Returns a readable string representation of the customer.
        return f"{self.full_name} ({self.username})"

    def set_password(self, raw_password: str) -> None:  # Hashes and stores the customer's password.
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:  # Verifies the provided password against the stored hash.
        return check_password(raw_password, self.password)

    @staticmethod
    def generate_customer_code() -> str:  # Generates a unique customer code.
        while True:
            code = f"CUST-{secrets.randbelow(1_000_000):06d}"
            if not Customer.objects.filter(customer_code=code).exists():
                return code

    @property
    def primary_account(self):  # Returns the customer's first active account or the first available account.
        accounts = list(self.accounts.all())
        for account in accounts:
            if account.status == account.Status.ACTIVE:
                return account
        return accounts[0] if accounts else None

    @property
    def display_role(self) -> str:  # Returns the customer's role name.
        return "Customer"

    def save(self, *args, **kwargs):  # Saves the customer after generating a customer code if needed.
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        super().save(*args, **kwargs)
