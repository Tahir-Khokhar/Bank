from __future__ import annotations

from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Customer(models.Model):

    full_name = models.CharField(max_length=150)  # Store customer full name
    username = models.CharField(max_length=150, unique=True)  # Store unique username
    email = models.EmailField(max_length=254, unique=True)  # Store unique email
    password = models.CharField(max_length=255)  # Store hashed password

    is_active = models.BooleanField(default=True)  # Store account status
    created_at = models.DateTimeField(auto_now_add=True)  # Save account creation time
    updated_at = models.DateTimeField(auto_now=True)  # Update modified time

    class Meta:  # Define model settings
        verbose_name = "Customer"  # Set model display name
        verbose_name_plural = "Customers"  # Set plural display name

    def __str__(self) -> str:  # Return customer name as a string
        return f"{self.full_name} ({self.username})"  # Return customer name

    def set_password(self, raw_password: str) -> None:  # Set hashed password
        self.password = make_password(raw_password)  # Hash password

    def check_password(self, raw_password: str) -> bool:  # Check entered password
        return check_password(raw_password, self.password)  # Verify password
