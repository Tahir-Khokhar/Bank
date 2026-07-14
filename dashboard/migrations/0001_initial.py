import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0002_customer_profile"),
        ("employees", "0002_employee_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("audience", models.CharField(choices=[("customer", "Customer"), ("employee", "Employee")], max_length=10)),
                ("category", models.CharField(choices=[("transaction", "Transaction"), ("loan", "Loan"), ("account", "Account"), ("system", "System"), ("message", "Message")], default="system", max_length=15)),
                ("title", models.CharField(max_length=150)),
                ("message", models.TextField(blank=True)),
                ("url", models.CharField(blank=True, max_length=255)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="customers.customer")),
                ("employee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="employees.employee")),
            ],
            options={"verbose_name": "Notification", "verbose_name_plural": "Notifications", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("actor_role", models.CharField(blank=True, max_length=20)),
                ("actor_name", models.CharField(blank=True, max_length=150)),
                ("category", models.CharField(choices=[("auth", "Authentication"), ("transaction", "Transaction"), ("loan", "Loan"), ("customer", "Customer"), ("employee", "Employee"), ("account", "Account"), ("system", "System")], default="system", max_length=15)),
                ("action", models.CharField(max_length=255)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to="customers.customer")),
                ("employee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to="employees.employee")),
            ],
            options={"verbose_name": "Activity Log", "verbose_name_plural": "Activity Logs", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="notification", index=models.Index(fields=["audience", "is_read"], name="dashboard_n_audienc_3f2a1c_idx")),
    ]
