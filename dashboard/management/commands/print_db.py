from __future__ import annotations

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print all rows of every model directly to the terminal."

    def handle(self, *args, **options):
        model_list = [m for m in apps.get_models() if not m._meta.abstract]

        for model in model_list:
            fields = [
                f.name
                for f in model._meta.get_fields()
                if getattr(f, "concrete", False) and not f.many_to_many
            ]
            rows = list(model.objects.all().values(*fields))
            count = len(rows)

            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"=== {model._meta.label} ({count} row(s)) ==="))
            if not rows:
                continue

            self.stdout.write(self.style.MIGRATE_HEADING(" | ".join(fields)))
            for row in rows:
                self.stdout.write(
                    " | ".join("" if row[f] is None else str(row[f]) for f in fields)
                )
