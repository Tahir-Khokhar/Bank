from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("customers", "0002_customer_profile"),
        ("employees", "0002_employee_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="Loan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(blank=True, max_length=40, unique=True)),
                ("loan_type", models.CharField(choices=[("personal", "Personal Loan"), ("home", "Home Loan"), ("car", "Car Loan"), ("business", "Business Loan"), ("education", "Education Loan")], default="personal", max_length=20)),
                ("principal_amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("interest_rate", models.DecimalField(decimal_places=2, default=Decimal("12.00"), help_text="Annual interest rate (%)", max_digits=5)),
                ("tenure_months", models.PositiveIntegerField(default=12)),
                ("emi_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15)),
                ("total_payable", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15)),
                ("amount_paid", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15)),
                ("purpose", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("under_review", "Under Review"), ("approved", "Approved"), ("rejected", "Rejected"), ("disbursed", "Disbursed"), ("active", "Active"), ("closed", "Closed"), ("defaulted", "Defaulted")], default="pending", max_length=20)),
                ("decision_note", models.CharField(blank=True, max_length=255)),
                ("applied_at", models.DateTimeField(auto_now_add=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("disbursed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="loans", to="accounts.account")),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="loans", to="customers.customer")),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_loans", to="employees.employee")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_loans", to="employees.employee")),
            ],
            options={"verbose_name": "Loan", "verbose_name_plural": "Loans", "ordering": ["-applied_at"]},
        ),
        migrations.CreateModel(
            name="LoanRepayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("method", models.CharField(choices=[("account", "Account Debit"), ("cash", "Cash"), ("online", "Online")], default="account", max_length=10)),
                ("reference", models.CharField(blank=True, max_length=40)),
                ("paid_at", models.DateTimeField(auto_now_add=True)),
                ("loan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="repayments", to="loans.loan")),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="recorded_repayments", to="employees.employee")),
            ],
            options={"verbose_name": "Loan Repayment", "verbose_name_plural": "Loan Repayments", "ordering": ["-paid_at"]},
        ),
        migrations.AddIndex(model_name="loan", index=models.Index(fields=["reference"], name="loans_loan_referen_a1b2c3_idx")),
        migrations.AddIndex(model_name="loan", index=models.Index(fields=["status"], name="loans_loan_status_d4e5f6_idx")),
    ]
