"""
Tests for the ``seed_licenses`` management command (FR-007a, D-018, R4).
"""

import pytest
from django.core.management import call_command
from licensing.models import License

from fairdm.core.dataset.models import get_default_license_pk
from fairdm.management.commands.seed_licenses import RECOMMENDED_LICENSE_NAMES


@pytest.mark.django_db
class TestSeedLicensesFromAnEmptyDatabase:
    """T094: from an empty database, standing up a portal makes the
    recommended licences available and the configured default resolves."""

    def test_recommended_licenses_are_created(self):
        License.objects.all().delete()

        call_command("seed_licenses", verbosity=0)

        assert set(
            License.objects.filter(
                name__in=RECOMMENDED_LICENSE_NAMES
            ).values_list("name", flat=True)
        ) == RECOMMENDED_LICENSE_NAMES

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
    """T095: running the command twice changes nothing, including a
    licence the portal has edited."""

    def test_running_twice_creates_no_duplicates(self):
        License.objects.all().delete()

        call_command("seed_licenses", verbosity=0)
        call_command("seed_licenses", verbosity=0)

        assert (
            License.objects.filter(name__in=RECOMMENDED_LICENSE_NAMES).count() == 3
        )

    def test_an_edited_licence_survives_a_second_run(self):
        License.objects.all().delete()
        call_command("seed_licenses", verbosity=0)

        edited = License.objects.get(name="CC BY 4.0")
        edited.description = "A portal-specific description of CC BY 4.0."
        edited.save()

        call_command("seed_licenses", verbosity=0)

        edited.refresh_from_db()
        assert edited.description == "A portal-specific description of CC BY 4.0."


@pytest.mark.django_db
class TestAPortalThatDeclinesTheStep:
    """T096: a portal that drops the step from its settings does not get
    the recommended licences - nothing else creates them."""

    def test_no_other_setup_step_seeds_the_licences(self, settings):
        """Run the deploy pipeline with the licence step declined, and the
        recommended licences stay absent. This is the half FR-007a makes a
        requirement: seeding is a recommendation the portal may drop, so it
        must not be smuggled in by a step it cannot drop.
        """
        License.objects.all().delete()

        always_run = settings.DJANGO_SETUP_TOOLS[""]["always_run"]
        assert ("seed_licenses",) in always_run, (
            "the step being declined is not in always_run - see "
            "TestSeedLicensesInThePipeline"
        )

        # The framework steps are the test harness's own job and say nothing about
        # licences; what is worth running is every other step that loads reference
        # data, `preload` above all.
        framework_steps = {"migrate", "collectstatic"}
        remaining = [
            step
            for step in always_run
            if isinstance(step, tuple)
            and step != ("seed_licenses",)
            and step[0] not in framework_steps
        ]
        assert remaining, "no reference-data step left to run - the guard is vacuous"

        for step in remaining:
            call_command(*step, verbosity=0)

        assert License.objects.filter(name__in=RECOMMENDED_LICENSE_NAMES).count() == 0

    def test_the_command_is_what_creates_them(self):
        """The control for the test above: the same empty database, the one
        declined step run, and the licences appear.
        """
        License.objects.all().delete()

        call_command("seed_licenses", verbosity=0)

        assert License.objects.filter(name__in=RECOMMENDED_LICENSE_NAMES).count() == 3


class TestSeedLicensesInThePipeline:
    """T098: the step runs in ``always_run``, beside ``preload`` - not
    ``on_initial`` - so an *existing* portal gets it on its next deploy,
    not only a freshly created one (D-018)."""

    def test_seed_licenses_is_declared_in_always_run(self, settings):
        always_run = settings.DJANGO_SETUP_TOOLS[""]["always_run"]
        assert ("seed_licenses",) in always_run

    def test_seed_licenses_is_not_declared_in_on_initial(self, settings):
        on_initial = settings.DJANGO_SETUP_TOOLS[""]["on_initial"]
        assert ("seed_licenses",) not in on_initial
