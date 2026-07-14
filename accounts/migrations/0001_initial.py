from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Branch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("code", models.CharField(max_length=20, unique=True)),
                ("address", models.CharField(blank=True, max_length=255)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Branch", "verbose_name_plural": "Branches", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Account",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_number", models.CharField(blank=True, max_length=24, unique=True)),
                ("account_type", models.CharField(choices=[("savings", "Savings"), ("current", "Current"), ("fixed", "Fixed Deposit"), ("salary", "Salary")], default="savings", max_length=20)),
                ("balance", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15)),
                ("hold_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15)),
                ("status", models.CharField(choices=[("active", "Active"), ("frozen", "Frozen"), ("inactive", "Inactive"), ("closed", "Closed")], default="active", max_length=20)),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="accounts", to="accounts.branch")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="accounts", to="customers.customer")),
            ],
            options={"verbose_name": "Account", "verbose_name_plural": "Accounts", "ordering": ["-opened_at"]},
        ),
        migrations.AddIndex(
            model_name="account",
            index=models.Index(fields=["account_number"], name="accounts_ac_account_2b5d9c_idx"),
        ),
        migrations.AddIndex(
            model_name="account",
            index=models.Index(fields=["status"], name="accounts_ac_status_9f1a7d_idx"),
        ),
    ]
