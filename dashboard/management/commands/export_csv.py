from __future__ import annotations

import csv
import os

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Export every model in the database to individual CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default="db_export",
            help="Output directory for the CSV files (default: db_export).",
        )

    def handle(self, *args, **options):
        out_dir = options["out"]
        os.makedirs(out_dir, exist_ok=True)

        model_list = [m for m in apps.get_models() if not m._meta.abstract]

        for model in model_list:
            label = model._meta.label.replace(".", "_")
            path = os.path.join(out_dir, f"{label}.csv")
            fields = [
                f
                for f in model._meta.get_fields()
                if getattr(f, "concrete", False) and not f.many_to_many
            ]
            field_names = [f.name for f in fields]

            rows = model.objects.all().values(*field_names)

            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=field_names)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

            count = model.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f"{label}: {count} row(s) -> {path}")
            )

        self.stdout.write(self.style.SUCCESS(f"Export complete in '{out_dir}'."))
