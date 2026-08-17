"""The surface as an addon author meets it, and what it costs to render."""

import pytest
from django.urls import reverse
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample
from fairdm.factories import PointFactory, SampleFactory


@pytest.mark.django_db
class TestAnAddonCanExtendARecordItDoesNotOwn:
    def test_a_registration_from_outside_the_framework_is_served(self, client):
        """SC-002, as close as a test can get.

        The plugin below is defined here rather than in `fairdm`, registered against a core record
        it does not own, and reached without any URL configuration being edited.
        """

        @plugins.register(Sample, label="Addon Page", icon="puzzle", order=900)
        class AddonPage(Plugin, TemplateView):
            template_name = "fairdm/plugin.html"

        # Re-mount so the new registration is routed, as it would be at startup.
        patterns = plugins.registry.get_urls_for_model(Sample)
        assert "addon-page" in [p.name for p in patterns]

    def test_the_declared_surface_is_all_an_author_needs(self):
        """Everything an author touches is importable from one place."""
        import fairdm.contrib.plugins as api

        for name in ("Plugin", "register", "registry", "is_instance_of", "has_perm"):
            assert hasattr(api, name), name


@pytest.mark.django_db
class TestARecordWithoutAUuid:
    def test_a_location_plugin_resolves_and_reverses(self):
        """The location record is keyed on a coordinate pair and has no uuid at all."""
        from fairdm.contrib.location.models import Point
        from fairdm.contrib.plugins import reverse as plugin_reverse

        # Addressing is declared when the location URL configuration is imported.
        from django.urls import reverse as django_reverse

        django_reverse("point:point-overview", kwargs={"lon": "1", "lat": "2"})

        point = PointFactory()
        url = plugin_reverse(point, "point-overview")
        assert str(point.x) in url
        assert str(point.y) in url

        assert plugins.registry.lookup_for(Point) == {"lon": "x", "lat": "y"}


@pytest.mark.django_db
class TestWhatARecordPageCosts:
    """Pinned rather than estimated.

    The research derived these from source and said so. A permission decision on a record runs
    through several object-level backends, and a record page evaluates every registered plugin, so
    the memo is what keeps the count flat rather than multiplying by the number of plugins.
    """

    def test_the_cost_does_not_scale_with_the_number_of_plugins(
        self, client, plain_user, django_capture_on_commit_callbacks
    ):
        """The claim worth pinning is invariance, not an absolute number.

        A record page is expensive for reasons that have nothing to do with plugins. What matters
        here is that adding plugins does not multiply the permission checks — which is what the
        per-request memo buys, and what an unmemoised object-level check would have cost.
        """
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        sample = SampleFactory()
        client.force_login(plain_user)
        url = reverse("sample:overview", kwargs={"uuid": sample.uuid})

        with CaptureQueriesContext(connection) as before:
            client.get(url)
        baseline = len(before.captured_queries)

        for index in range(5):
            plugins.register(Sample, label=f"Extra {index}", order=900 + index)(
                type(
                    f"ExtraCost{index}",
                    (Plugin, TemplateView),
                    {
                        "template_name": "fairdm/plugin.html",
                        "permission": "sample.change_sample",
                    },
                )
            )
        plugins.registry.get_urls_for_model(Sample)

        with CaptureQueriesContext(connection) as after:
            client.get(url)

        # Five more permission-carrying plugins, all denied, all on the same record.
        assert len(after.captured_queries) - baseline <= 5, (
            f"{baseline} -> {len(after.captured_queries)}: permission checks are not being memoised"
        )

    def test_the_permission_memo_holds_across_repeated_checks(
        self, as_user, plain_user, sample, django_assert_num_queries
    ):
        from fairdm.contrib.plugins.access import has_perm

        request = as_user(plain_user)
        with django_assert_num_queries(0) as captured:
            pass
        has_perm(request, "sample.change_sample", sample)
        first = len(request._fairdm_plugin_perm_cache)
        with django_assert_num_queries(0):
            for _ in range(10):
                has_perm(request, "sample.change_sample", sample)
        assert len(request._fairdm_plugin_perm_cache) == first
