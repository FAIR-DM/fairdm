"""Management command that removes permission rows no model declares."""

from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Delete permissions that are not in any model's default_permissions or Meta.permissions."""

    help = "Remove any permissions not defined in models' default_permissions or Meta.permissions."

    def handle(self, *args, **options):
        """Find and delete the stale permissions."""
        self.stdout.write(self.style.WARNING("Scanning for unused permissions..."))

        expected_perms = set()

        for model in apps.get_models():
            opts = model._meta
            ct = ContentType.objects.get_for_model(model)

            for action in opts.default_permissions:
                expected_perms.add((ct.id, f"{action}_{opts.model_name}"))

            for codename, _ in opts.permissions:
                expected_perms.add((ct.id, codename))

        all_perms = Permission.objects.all()

        stale_perms = [
            perm
            for perm in all_perms
            if (perm.content_type_id, perm.codename) not in expected_perms
        ]

        if not stale_perms:
            self.stdout.write(self.style.SUCCESS("No stale permissions found."))
            return

        self.stdout.write(f"Found {len(stale_perms)} stale permissions:")
        for perm in stale_perms:
            self.stdout.write(f"  {perm.content_type.app_label}.{perm.codename}")

        deleted_count, _ = Permission.objects.filter(
            id__in=[p.id for p in stale_perms]
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted_count} stale permissions.")
        )
