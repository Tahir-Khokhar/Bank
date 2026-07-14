from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("employees", "0002_employee_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(blank=True, max_length=40, unique=True)),
                ("txn_type", models.CharField(choices=[("deposit", "Deposit"), ("withdrawal", "Withdrawal"), ("transfer", "Transfer"), ("fee", "Fee"), ("loan_disbursement", "Loan Disbursement"), ("loan_repayment", "Loan Repayment"), ("reversal", "Reversal")], max_length=20)),
                ("direction", models.CharField(choices=[("credit", "Credit"), ("debit", "Debit")], max_length=10)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("fee", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15)),
                ("balance_after", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=15)),
                ("status", models.CharField(choices=[("success", "Success"), ("pending", "Pending"), ("failed", "Failed"), ("reversed", "Reversed")], default="success", max_length=10)),
                ("channel", models.CharField(choices=[("online", "Online"), ("teller", "Teller"), ("atm", "ATM"), ("system", "System")], default="online", max_length=10)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("is_reversed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="accounts.account")),
                ("counterparty_account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="counterparty_transactions", to="accounts.account")),
                ("created_by_employee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_transactions", to="employees.employee")),
                ("related_transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="linked_entries", to="transactions.transaction")),
            ],
            options={"verbose_name": "Transaction", "verbose_name_plural": "Transactions", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="transaction", index=models.Index(fields=["reference"], name="transaction_referen_5c7a1b_idx")),
        migrations.AddIndex(model_name="transaction", index=models.Index(fields=["txn_type"], name="transaction_txn_typ_2d8e4f_idx")),
        migrations.AddIndex(model_name="transaction", index=models.Index(fields=["status"], name="transaction_status_7a3c9e_idx")),
        migrations.AddIndex(model_name="transaction", index=models.Index(fields=["created_at"], name="transaction_created_1b6d2a_idx")),
    ]
