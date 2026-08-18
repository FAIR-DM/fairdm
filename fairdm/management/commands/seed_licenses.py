"""Seed the licences FairDM recommends (FR-007a, D-018, research.md R4).

``django-content-license`` ships the Creative Commons licence text and
declines to load any of it - curating which licences a portal offers is a
decision for the portal, not the library. Nothing in FairDM loaded that
fixture either, so a freshly migrated portal had no ``License`` rows at
all: ``FAIRDM_DEFAULT_LICENSE`` silently resolved to nothing, and any form
built over ``License.objects.all()`` was a required field with an empty
queryset.

This command creates the three licences FairDM recommends - CC0 1.0,
CC BY 4.0 and CC BY-SA 4.0 - reading their name, description, licence text
and canonical URL straight out of ``django-content-license``'s own
``fixtures/creativecommons.json.gz``, rather than retyping them. The NC and
ND variants that fixture also carries are deliberately not seeded: they
fail the Open Definition, and a framework named for reusability should not
present "no derivatives" as a recommendation for research data. A portal
that wants one adds it itself.

It runs in the deployment pipeline's ``always_run`` step
(``fairdm/conf/settings/apps.py``, ``DJANGO_SETUP_TOOLS``), beside the
vocabulary ``preload`` step, so an *existing* portal picks it up on its
next deploy and not only a freshly created one. It is idempotent, keyed on
``License.name`` (``unique=True`` on ``licensing.models.License``), and
leaves alone a licence a portal has already edited under one of these
three names.

Usage::

    python manage.py seed_licenses
"""

import gzip
import json
from pathlib import Path

import licensing
from django.core.management.base import BaseCommand
from licensing.models import License

#: The names of the licences FairDM recommends. `django-content-license`'s
#: fixture also carries the NC and ND variants under other names - see the
#: module docstring for why those are excluded.
RECOMMENDED_LICENSE_NAMES = {"CC0 1.0", "CC BY 4.0", "CC BY-SA 4.0"}


def _recommended_license_fields():
    """Read the recommended licences' field values out of
    `django-content-license`'s own fixture rather than retyping the licence
    text and canonical URLs by hand.
    """
    fixture_path = (
        Path(licensing.__file__).parent / "fixtures" / "creativecommons.json.gz"
    )
    # That path is internal to `django-content-license`, so a release of it that moves
    # or drops the file is a possibility this command has to survive. It runs on every
    # deploy, and the licences it seeds are a recommendation a portal may decline
    # (FR-007a), so a missing fixture is a degraded deploy rather than a failed one.
    try:
        with gzip.open(fixture_path, "rt", encoding="utf-8") as fixture_file:
            rows = json.load(fixture_file)
    except (OSError, ValueError):
        return None
    return [
        row["fields"]
        for row in rows
        if row["model"] == "licensing.license"
        and row["fields"]["name"] in RECOMMENDED_LICENSE_NAMES
    ]


class Command(BaseCommand):
    help = "Create the licences FairDM recommends (CC0 1.0, CC BY 4.0, CC BY-SA 4.0)."

    def handle(self, *args, **options):
        recommended = _recommended_license_fields()
        if recommended is None:
            self.stderr.write(
                self.style.WARNING(
                    "Could not read the licence fixture from django-content-license; "
                    "no licences were seeded. A portal can create them by hand."
                )
            )
            return

        for fields in recommended:
            name = fields["name"]
            _license, created = License.objects.get_or_create(
                name=name,
                defaults={
                    "canonical_url": fields["canonical_url"],
                    "description": fields.get("description", ""),
                    "text": fields["text"],
                    "is_active": fields.get("is_active", True),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created licence '{name}'."))
            else:
                self.stdout.write(f"Licence '{name}' already exists; left unchanged.")
