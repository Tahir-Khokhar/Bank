from __future__ import annotations

from django.core.management.base import BaseCommand
from employees.models import Employee


class Command(BaseCommand):
    help = "Delete 51 regular (non-manager) employees, keeping the manager login intact."

    def handle(self, *args, **options):
        # Keep managers so admin/employee dashboards stay usable.
        queryset = Employee.objects.filter(role=Employee.Role.EMPLOYEE).order_by("pk")
        total = queryset.count()
        to_delete = min(51, total)

        ids = list(queryset.values_list("pk", flat=True)[:to_delete])
        deleted, _ = Employee.objects.filter(pk__in=ids).delete()

        remaining = Employee.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} employee(s). {remaining} employee(s) remaining."
            )
        )
