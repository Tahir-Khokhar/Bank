import secrets

import django.db.models.deletion
from django.db import migrations, models


def populate_employee_codes(apps, schema_editor):
    Employee = apps.get_model("employees", "Employee")
    used = set(
        Employee.objects.exclude(employee_code="").values_list("employee_code", flat=True)
    )
    for employee in Employee.objects.filter(employee_code=""):
        while True:
            code = f"EMP-{secrets.randbelow(1_000_000):06d}"
            if code not in used:
                used.add(code)
                break
        employee.employee_code = code
        employee.save(update_fields=["employee_code"])


def promote_first_manager(apps, schema_editor):
    """Ensure at least one branch manager exists so the admin dashboard works."""
    Employee = apps.get_model("employees", "Employee")
    if not Employee.objects.filter(role="manager").exists():
        first = Employee.objects.order_by("id").first()
        if first:
            first.role = "manager"
            first.can_approve_loans = True
            first.can_reverse_transactions = True
            first.save(update_fields=["role", "can_approve_loans", "can_reverse_transactions"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("employees", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="employee_code",
            field=models.CharField(blank=True, default="", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="role",
            field=models.CharField(choices=[("manager", "Branch Manager"), ("employee", "Employee")], default="employee", max_length=20),
        ),
        migrations.AddField(
            model_name="employee",
            name="position",
            field=models.CharField(blank=True, default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="cnic",
            field=models.CharField(blank=True, default="", max_length=30, verbose_name="CNIC / National ID"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="address",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="employee",
            name="profile_picture",
            field=models.ImageField(blank=True, null=True, upload_to="profiles/employees/"),
        ),
        migrations.AddField(
            model_name="employee",
            name="branch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="employees", to="accounts.branch"),
        ),
        migrations.AddField(
            model_name="employee",
            name="can_approve_loans",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="employee",
            name="can_reverse_transactions",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="employee",
            name="is_suspended",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterModelOptions(
            name="employee",
            options={"ordering": ["-created_at"], "verbose_name": "Employee", "verbose_name_plural": "Employees"},
        ),
        migrations.RunPython(populate_employee_codes, noop),
        migrations.RunPython(promote_first_manager, noop),
        migrations.AlterField(
            model_name="employee",
            name="employee_code",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
