import secrets

import django.db.models.deletion
from django.db import migrations, models


def populate_customer_codes(apps, schema_editor):
    Customer = apps.get_model("customers", "Customer")
    used = set(
        Customer.objects.exclude(customer_code="").values_list("customer_code", flat=True)
    )
    for customer in Customer.objects.filter(customer_code=""):
        while True:
            code = f"CUST-{secrets.randbelow(1_000_000):06d}"
            if code not in used:
                used.add(code)
                break
        customer.customer_code = code
        customer.save(update_fields=["customer_code"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("customers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="customer_code",
            field=models.CharField(blank=True, default="", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customer",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customer",
            name="cnic",
            field=models.CharField(blank=True, default="", max_length=30, verbose_name="CNIC / National ID"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customer",
            name="address",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customer",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="occupation",
            field=models.CharField(blank=True, default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customer",
            name="monthly_income",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="employer_name",
            field=models.CharField(blank=True, default="", max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customer",
            name="profile_picture",
            field=models.ImageField(blank=True, null=True, upload_to="profiles/customers/"),
        ),
        migrations.AddField(
            model_name="customer",
            name="branch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="customers", to="accounts.branch"),
        ),
        migrations.AlterModelOptions(
            name="customer",
            options={"ordering": ["-created_at"], "verbose_name": "Customer", "verbose_name_plural": "Customers"},
        ),
        migrations.RunPython(populate_customer_codes, noop),
        migrations.AlterField(
            model_name="customer",
            name="customer_code",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
