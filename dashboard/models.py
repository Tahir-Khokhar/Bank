# Enable postponed evaluation of type hints
from __future__ import annotations

# Import Django's model classes
from django.db import models


# Store notifications for customers and employees
class Notification(models.Model):
    """An in-app notification for a customer or an employee."""

    # Define notification audience choices
    class Audience(models.TextChoices):

        # Notification is for a customer
        CUSTOMER = "customer", "Customer"

        # Notification is for an employee
        EMPLOYEE = "employee", "Employee"

    # Define notification category choices
    class Category(models.TextChoices):

        # Transaction-related notification
        TRANSACTION = "transaction", "Transaction"

        # Loan-related notification
        LOAN = "loan", "Loan"

        # Account-related notification
        ACCOUNT = "account", "Account"

        # System notification
        SYSTEM = "system", "System"

        # General message notification
        MESSAGE = "message", "Message"

    # Store the notification audience
    audience = models.CharField(max_length=10, choices=Audience.choices)

    # Link the notification to a customer
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # Link the notification to an employee
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # Store the notification category
    category = models.CharField(
        max_length=15,
        choices=Category.choices,
        default=Category.SYSTEM,
    )

    # Store the notification title
    title = models.CharField(max_length=150)

    # Store the notification message
    message = models.TextField(blank=True)

    # Store the URL to open when the notification is clicked
    url = models.CharField(max_length=255, blank=True)

    # Track whether the notification has been read
    is_read = models.BooleanField(default=False)

    # Store the creation date automatically
    created_at = models.DateTimeField(auto_now_add=True)

    # Configure model settings
    class Meta:

        # Set the singular model name
        verbose_name = "Notification"

        # Set the plural model name
        verbose_name_plural = "Notifications"

        # Show newest notifications first
        ordering = ["-created_at"]

        # Create a database index for faster searches
        indexes = [
            models.Index(fields=["audience", "is_read"]),
        ]

    # Return a readable string for the notification
    def __str__(self) -> str:
        return f"{self.title} ({self.audience})"

    # Return the Bootstrap icon for the notification category
    @property
    def icon(self) -> str:
        return {
            self.Category.TRANSACTION: "bi-arrow-left-right",
            self.Category.LOAN: "bi-cash-coin",
            self.Category.ACCOUNT: "bi-person-vcard",
            self.Category.SYSTEM: "bi-gear",
            self.Category.MESSAGE: "bi-envelope",
        }.get(self.category, "bi-bell")


# Store activity logs for auditing system actions
class ActivityLog(models.Model):
    """An audit-trail record for actions across the system."""

    # Define activity categories
    class Category(models.TextChoices):

        # Authentication activity
        AUTH = "auth", "Authentication"

        # Transaction activity
        TRANSACTION = "transaction", "Transaction"

        # Loan activity
        LOAN = "loan", "Loan"

        # Customer activity
        CUSTOMER = "customer", "Customer"

        # Employee activity
        EMPLOYEE = "employee", "Employee"

        # Account activity
        ACCOUNT = "account", "Account"

        # System activity
        SYSTEM = "system", "System"

    # Store the actor's role
    actor_role = models.CharField(max_length=20, blank=True)

    # Store the actor's name
    actor_name = models.CharField(max_length=150, blank=True)

    # Link the activity to a customer
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    # Link the activity to an employee
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )

    # Store the activity category
    category = models.CharField(
        max_length=15,
        choices=Category.choices,
        default=Category.SYSTEM,
    )

    # Store the action description
    action = models.CharField(max_length=255)

    # Store the user's IP address
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Store the creation date automatically
    created_at = models.DateTimeField(auto_now_add=True)

    # Configure model settings
    class Meta:

        # Set the singular model name
        verbose_name = "Activity Log"

        # Set the plural model name
        verbose_name_plural = "Activity Logs"

        # Show newest activity first
        ordering = ["-created_at"]

    # Return a readable string for the activity log
    def __str__(self) -> str:
        return f"{self.actor_name}: {self.action}"

    # Return the Bootstrap icon for the activity category
    @property
    def icon(self) -> str:
        return {
            self.Category.AUTH: "bi-box-arrow-in-right",
            self.Category.TRANSACTION: "bi-arrow-left-right",
            self.Category.LOAN: "bi-cash-coin",
            self.Category.CUSTOMER: "bi-people",
            self.Category.EMPLOYEE: "bi-person-badge",
            self.Category.ACCOUNT: "bi-person-vcard",
            self.Category.SYSTEM: "bi-gear",
        }.get(self.category, "bi-activity")
