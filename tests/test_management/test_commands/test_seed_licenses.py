"""Tests for the ``seed_licenses`` management command (FR-007a, D-018, R4)."""

import pytest
from django.core.management import call_command
from licensing.models import License

from fairdm.core.dataset.models import get_default_license_pk
from fairdm.management.commands.seed_licenses import RECOMMENDED_LICENSE_NAMES


@pytest.mark.django_db
class TestSeedLicensesFromAnEmptyDatabase:
    def test_recommended_licenses_are_created(self):
        License.objects.all().delete()

        call_command("seed_licenses", verbosity=0)

        assert (
            set(
                License.objects.filter(name__in=RECOMMENDED_LICENSE_NAMES).values_list(
                    "name", flat=True
                )
            )
            == RECOMMENDED_LICENSE_NAMES
        )

    def test_the_configured_default_resolves(self):
        License.objects.all().delete()

        call_command("seed_licenses", verbosity=0)

        default_pk = get_default_license_pk()
        assert default_pk is not None
        assert License.objects.get(pk=default_pk).name == "CC BY 4.0"

    def test_the_nc_and_nd_variants_are_not_seeded(self):
        License.objects.all().delete()

        call_command("seed_licenses", verbosity=0)

        names = set(License.objects.values_list("name", flat=True))
        assert "CC BY-NC 4.0" not in names
        assert "CC BY-ND 4.0" not in names
        assert "CC BY-NC-SA 4.0" not in names
        assert "CC BY-NC-ND 4.0" not in names


@pytest.mark.django_db
class TestSeedLicensesIsIdempotent:
    def test_running_twice_creates_no_duplicates(self):
        License.objects.all().delete()

        call_command("seed_licenses", verbosity=0)
        call_command("seed_licenses", verbosity=0)

        assert License.objects.filter(name__in=RECOMMENDED_LICENSE_NAMES).count() == 3

    def test_an_edited_licence_survives_a_second_run(self):
        License.objects.all().delete()
        call_command("seed_licenses", verbosity=0)

        edited = License.objects.get(name="CC BY 4.0")
        edited.description = "A portal-specific description of CC BY 4.0."
        edited.save()

        call_command("seed_licenses", verbosity=0)

        edited.refresh_from_db()
        assert edited.description == "A portal-specific description of CC BY 4.0."
