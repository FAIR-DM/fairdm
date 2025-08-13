from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Remove any permissions not defined in models' default_permissions or Meta.permissions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Scanning for unused permissions..."))

        expected_perms = set()

        # Collect expected permissions from all installed models
        for model in apps.get_models():
            opts = model._meta
            ct = ContentType.objects.get_for_model(model)

            # Default add/change/delete/view permissions
            for action in opts.default_permissions:
                expected_perms.add((ct.id, f"{action}_{opts.model_name}"))

            # Any custom Meta.permissions
            for codename, _ in opts.permissions:
                expected_perms.add((ct.id, codename))

        # Find all permissions in DB
        all_perms = Permission.objects.all()

        stale_perms = [perm for perm in all_perms if (perm.content_type_id, perm.codename) not in expected_perms]

        if not stale_perms:
            self.stdout.write(self.style.SUCCESS("No stale permissions found."))
            return

        self.stdout.write(f"Found {len(stale_perms)} stale permissions:")
        for perm in stale_perms:
            self.stdout.write(f"  {perm.content_type.app_label}.{perm.codename}")

        # Delete them
        deleted_count, _ = Permission.objects.filter(id__in=[p.id for p in stale_perms]).delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} stale permissions."))
